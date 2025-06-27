from flask import request, jsonify
from . import api

polls = {
    "weekly-poll": {
        "question": "Which feature would you like to see next?",
        "options": [
            {"name": "New Feature A", "votes": 0},
            {"name": "New Feature B", "votes": 1},
            {"name": "New Feature C", "votes": 0}
        ]
    }
}

@api.route('/polls/<poll_id>', methods=['GET'])
def get_poll(poll_id):
    poll = polls.get(poll_id)
    if poll:
        return jsonify(poll)
    else:
        return jsonify({"error": "Poll not found"}), 404

@api.route('/polls/<poll_id>', methods=['PATCH'])
def vote(poll_id):
    poll = polls.get(poll_id)
    if poll:
        vote = request.json.get('vote')
        option = next((opt for opt in poll['options'] if opt['name'] == vote), None)
        if option:
            option['votes'] += 1
            return jsonify(poll)
        else:
            return jsonify({"error": "Invalid vote option"}), 400
    else:
        return jsonify({"error": "Poll not found"}), 404
