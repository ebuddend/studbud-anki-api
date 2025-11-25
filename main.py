from flask import Flask, request, send_file, jsonify
import genanki
import io
import random

app = Flask(__name__)

# Cloze model used for all StudBud decks
CLOZE_MODEL_ID = 1607392319

CLOZE_MODEL = genanki.Model(
    CLOZE_MODEL_ID,
    "StudBud Cloze Model",
    fields=[
        {"name": "Text"},
        {"name": "Extra"},
    ],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "{{cloze:Text}}",
            "afmt": "{{cloze:Text}}<br><br>{{Extra}}",
        },
    ],
    model_type=genanki.Model.CLOZE,
)


def make_deck_id() -> int:
    """Generate a random deck ID."""
    return random.randrange(1 << 30, 1 << 31)


@app.route("/generate-apkg", methods=["POST"])
def generate_apkg():
    try:
        # Get the JSON body with deckName + cards
        data = request.get_json(force=True)

        deck_name = data.get("deckName", "StudBud Deck")
        cards = data.get("cards", [])

        if not cards:
            return jsonify({"error": "No cards provided"}), 400

        # Create the deck
        deck = genanki.Deck(make_deck_id(), deck_name)

        # Add all cloze cards
        for card in cards:
            cloze_text = (card.get("cloze_text") or "").strip()
            extra = (card.get("extra") or "").strip()
            tags = card.get("tags") or []

            if not cloze_text:
                continue

            note = genanki.Note(
                model=CLOZE_MODEL,
                fields=[cloze_text, extra],
                tags=tags,
            )
            deck.add_note(note)

        # Build package into memory buffer
        package = genanki.Package(deck)
        buffer = io.BytesIO()
        package.write_to_file(buffer)
        buffer.seek(0)

        # Clean filename
        safe_name = (
            deck_name.replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            or "StudBud_Deck"
        )
        filename = f"{safe_name}.apkg"

        # Send APKG back to caller
        return send_file(
            buffer,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        # Return the error for debugging if something goes wrong
        return jsonify({"error": str(e)}), 500


# Local dev mode
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
