from flask import Flask, request, jsonify, redirect, render_template
from flask_caching import Cache
from psycopg import errors
import uuid
from DatabaseProvider import DatabaseProvider
from Shortner import TextShortener


app = Flask(__name__)

# Configure Flask-Caching (Simple in-memory cache for single-server setups)
# For production multi-server setups, change 'SimpleCache' to 'RedisCache'
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})


@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route('/tiny-url/create', methods=['POST'])
def create_tiny_url():
    # 1. Parse and validate incoming JSON data
    data = request.get_json() or {}
    long_url = data.get('longUrl')
    custom_alias = data.get('customAlias')
    db_provider = DatabaseProvider()
    user_id  = uuid.UUID(int=0)

    # 2. Check for required fields
    if not long_url:
        return jsonify({"error": "Missing required field: longUrl"}), 400

    # 3. Handle custom alias or generate a random one
    if custom_alias:
        # Strip whitespace and validate alias uniqueness
        custom_alias = custom_alias.strip()

        try:
            # Let the DB try to insert. It must have a UNIQUE constraint on 'alias'.
            db_provider.insert_sample_url(user_id, alias, long_url)

        except errors.UniqueViolation: 
            # Catch your specific DB driver's duplicate key exception
            return jsonify({"error": "Custom alias already exists"}), 409

        alias = custom_alias

    else:
        text_shortener = TextShortener()
        inserted = False
        
        while not inserted:
            alias = text_shortener.shorten(long_url)

            try:
                db_provider.insert_sample_url(user_id, alias, long_url)
                inserted = True
                
            except errors.UniqueViolation:
                # Loop repeats seamlessly if a collision occurs
                continue


    # 5. Construct the final response
    # request.host_url automatically includes http:// or https:// with the domain
    short_url = f"{request.host_url}redirect/{alias}"
    
    return jsonify({"shortUrl": short_url}), 201

# Clean suffix path match (e.g. /tiny-url/metadata/goog)
@app.route('/tiny-url/metadata/<alias>', methods=['GET'])
def get_url_metadata(alias):
    db_provider = DatabaseProvider()

    # Direct lookup using the suffix string
    record = db_provider.find_url_metadata(alias)
    if not record:
        return jsonify({"error": "Short URL metadata not found"}), 404

    return jsonify({
        "creationTime": record["creation_time"].isoformat(),
        "expireTime": record["expire_time"].isoformat(),
        "accessCount": record["access_count"],
        "shortUrl": record["short_url"],
        "longUrl": record["long_url"]
    }), 200

@app.route('/redirect/<alias>', methods=['GET'])
def redirect_to_long_url(alias):
    # 1. Check server-side cache first to avoid DB hits
    cache_key = f"url:{alias}"
    long_url = cache.get(cache_key)

    if not long_url:
        db_provider = DatabaseProvider()
        record = db_provider.find_url_metadata(alias)
        
        if not record:
            return jsonify({"error": "URL not found"}), 404
        
        long_url = record["long_url"]
        # Store in cache for 5 minutes (300 seconds)
        cache.set(cache_key, long_url, timeout=300)

    # 2. Async/Background Write: Increment access count in DB
    # Note: Because the DB read is bypassed on cache hits, this now runs 
    # independently without blocking the user response.
    db_provider = DatabaseProvider()
    db_provider.increment_access_count(alias)

    # 3. HTTP Client Caching: Use 302 (Found) instead of 301 (Moved Permanently).
    # 301 caches aggressively in browsers, preventing your counter from tracking clicks.
    # 302 forces browsers to re-verify the endpoint every time, keeping your analytics accurate.
    return redirect(long_url, code=302)

if __name__ == '__main__':
    app.run(debug=True)