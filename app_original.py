from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from confluent_kafka import Consumer, KafkaError
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Kafka configuration
kafka_conf = {
    'bootstrap.servers': '192.168.1.7:9092',  # Replace with your Kafka broker address
    'group.id': 'my_group',  # Replace with your group ID
    'auto.offset.reset': 'latest'
}

# Kafka topic for messages
kafka_topic = 'drishti_topic'

# Create Kafka consumer
consumer = Consumer(kafka_conf)
consumer.subscribe([kafka_topic])

# Global variable to store the latest message
latest_message = None


# Consume messages
def consume_messages():
    global latest_message
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
            print(latest_message)


# Start consuming messages in a separate thread
consumer_thread = threading.Thread(target=consume_messages)
consumer_thread.daemon = True
consumer_thread.start()


# WebSocket route
@socketio.on('connect')
def handle_connect():
    global latest_message
    # Emit the initial message to the connected client
    emit('new_message', {'message': latest_message})


# Update the client with the latest message
@socketio.on('check_updates')
def handle_check_updates():
    global latest_message
    emit('new_message', {'message': latest_message})


@app.route('/')
def index():
    global latest_message
    return render_template('index.html', message=latest_message)


if __name__ == '__main__':
    socketio.run(app, debug=True)