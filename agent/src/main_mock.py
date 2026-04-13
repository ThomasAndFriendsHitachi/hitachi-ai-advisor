def worker():
    while True:
        try:
            # Pop task from Redis queue
            result = r.brpop(REDIS_QUEUE_NAME, timeout=5)

            if result: 
                _, message = result
                envelope = json.loads(message)
                
                # Extract the payload sent by the Express webhook
                payload = envelope.get('payload', {})

                # Map data for the DB columns
                project_name = payload.get('project_name', 'Unknown Project')
                risk_score = payload.get('risk_score', 'Medium') # From GH Action mock
                status = 'Pending Review' # Initial status
                
                print(f"Processing task for project: {project_name}")

                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Insert into specific columns + keep raw data for history
                        insert_query = """
                            INSERT INTO ai_tasks_results 
                            (project_name, risk_score, status, raw_payload) 
                            VALUES (%s, %s, %s, %s) 
                            RETURNING id;
                        """
                        cur.execute(insert_query, (
                            project_name, 
                            risk_score, 
                            status, 
                            json.dumps(payload)
                        ))
                        new_id = cur.fetchone()[0]
                        conn.commit()

                # Notify frontend via Redis Pub/Sub
                r.publish(REDIS_CHANNEL_NAME, json.dumps({"db_id": str(new_id), "status": "updated"}))
                print(f"Task {new_id} saved to DB and broadcasted.")

        except Exception as e:
            print(f"Worker Error: {e}")
            time.sleep(2)