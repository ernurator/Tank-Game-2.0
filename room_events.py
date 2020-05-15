import pika
import json
from threading import Thread

class RoomEvents(Thread):
    def __init__(self, room):
        super().__init__()
        self.room = room
        self.ready = False
        self.kill = False
        self.response = None
        self.new = False

    def run(self):
        self.credentials = pika.PlainCredentials('dar-tanks', password='5orPLExUYnyVYZg48caMpX')
        self.parameters = pika.ConnectionParameters('34.254.177.17', 5672, 'dar-tanks', self.credentials)
        self.connection = pika.BlockingConnection(self.parameters)

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True, auto_delete=True)
        self.events_queue = result.method.queue
        self.channel.exchange_declare('X:routing.topic', 'topic', durable=True)

        self.channel.queue_bind(exchange='X:routing.topic', queue=self.events_queue, routing_key=f'event.state.{self.room}')

        def on_response(ch, method, props, body):
            if self.kill:
                raise Exception('Consumer thread is killed')
            self.response = json.loads(body)
            self.new = True
            self.ready = True

        self.channel.basic_consume(
            queue=self.events_queue,
            on_message_callback=on_response,
            auto_ack=True)
        try:
            self.channel.start_consuming()
        except Exception as e:
            print(e)