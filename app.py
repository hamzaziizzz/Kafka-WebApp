import threading

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from confluent_kafka import Consumer, KafkaError

from feedback import STATUS, display_feedback

app = Flask(__name__)
socketio = SocketIO(app)

# Kafka configuration
kafka_conf = {
    'bootstrap.servers': '192.168.1.7:9092',  # Replace with your Kafka broker address
    'group.id': 'face_recognition_feedback_message_consumer_group',  # Replace with your group ID
    'auto.offset.reset': 'latest'
}

# Kafka topic for messages
kafka_topic = 'face_recognition_feedback_messages_topic_0'

# Create Kafka consumer
consumer = Consumer(kafka_conf)
consumer.subscribe([kafka_topic])

# Global variable to store the latest message
latest_message_to_display = None


# Consume messages
def consume_messages():
    global latest_message_to_display
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print("Reached end of partition")
            else:
                print(f"Error while consuming: {msg.error()}")
        else:
            latest_message = msg.value().decode('utf-8')
            # print(f"Latest message: {latest_message}")
            message_to_display = display_feedback(latest_message)
            print(f"Latest message to display: {message_to_display}")


# Start consuming messages in a separate thread
consumer_thread = threading.Thread(target=consume_messages)
consumer_thread.daemon = True
consumer_thread.start()


# WebSocket route
@socketio.on('connect')
def handle_connect():
    global latest_message_to_display
    # Emit the initial message to the connected client
    emit('new_message', {'message': latest_message_to_display})


# Update the client with the latest message
@socketio.on('check_updates')
def handle_check_updates():
    global latest_message_to_display
    emit('new_message', {'message': latest_message_to_display})


@app.route('/')
def index():
    global latest_message_to_display
    return render_template('index.html', message=latest_message_to_display)


if __name__ == '__main__':
    socketio.run(app, debug=True)