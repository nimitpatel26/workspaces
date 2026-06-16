from flask import Flask, request, jsonify, redirect, render_template
import uuid
from DatabaseProvider import DatabaseProvider
from Shortner import TextShortener


app = Flask(__name__)


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

    # 2. Check for required fields
    if not long_url:
        return jsonify({"error": "Missing required field: longUrl"}), 400

    # 3. Handle custom alias or generate a random one
    if custom_alias:
        # Strip whitespace and validate alias uniqueness
        custom_alias = custom_alias.strip()
        url_in_db = db_provider.find_url_metadata(custom_alias)

        if url_in_db:
            return jsonify({"error": "Custom alias already exists"}), 409
        alias = custom_alias

    else:
        text_Shortener = TextShortener()

        # Generate a unique random alias
        alias = text_Shortener.shorten(long_url)
        url_in_db = db_provider.find_url_metadata(alias)

        while url_in_db:
            alias = text_Shortener.shorten(long_url)
            url_in_db = db_provider.find_url_metadata(alias)

    user_id  = uuid.UUID(int=0)

    # 4. Store the mapping
    db_provider.insert_sample_url(str(user_id), alias, long_url)

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

if __name__ == '__main__':
    app.run(debug=True)