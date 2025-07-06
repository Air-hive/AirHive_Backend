from models import JobModel
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from app import app, db

# --- Create (POST) ---
@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    file_name = data.get('file_name')
    file_path =data.get('file_path')
    priority = data.get('priority')

    if not file_name or not file_path or not priority:
        return jsonify({'error': "Missing file name or file path or priority"}), 400

    new_job = JobModel(
        file_name=file_name,
        file_path=file_path,
        priority=priority
    )

    db.session.add(new_job)
    db.session.commit()
    return jsonify(new_job.to_dict()), 201

# --- Read All (GET) ---
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = JobModel.query.all()
    return jsonify([job.to_dict() for job in jobs])

# --- Read One (GET) ---
@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = JobModel.query.get_or_404(job_id)
    return jsonify(job.to_dict())

# --- Update (PUT) ---
@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    job = JobModel.query.get_or_404(job_id)
    data = request.get_json()
    job.file_name = data.get('file_name', job.file_name)
    job.file_path = data.get('file_path', job.file_path)
    job.priority = data.get('priority', job.priority)
    db.session.commit()
    return jsonify(job.to_dict())

# --- Delete (DELETE) ---
@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = JobModel.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"})