import unittest
from unittest.mock import patch
import signal
from worker.consumer import main

class TestConsumerMain(unittest.TestCase):

    @patch('worker.consumer.MinioClient')
    @patch('worker.consumer.RedisClient')
    @patch('worker.consumer.RabbitMQConsumer')
    @patch('worker.consumer.setup_observability')
    def test_main_initialization(self, mock_setup_observability, mock_rabbitmq, mock_redis, mock_minio):
        mock_consumer_instance = mock_rabbitmq.return_value
        
        main()

        mock_setup_observability.assert_called_once()
        mock_redis.assert_called_once()
        mock_rabbitmq.assert_called_once()
        mock_consumer_instance.start.assert_called_once()
        mock_minio.assert_called_once()

    @patch('worker.consumer.process_job_logic')
    @patch('worker.consumer.MinioClient')
    @patch('worker.consumer.RedisClient')
    @patch('worker.consumer.RabbitMQConsumer')
    def test_on_message_received_callback(self, mock_rabbitmq, mock_redis, mock_minio, mock_process_logic):
        mock_redis_instance = mock_redis.return_value
        mock_minio_instance = mock_minio.return_value # Istanza mockata di Minio
        
        main()
        
        args, kwargs = mock_rabbitmq.call_args
        callback_function = kwargs.get('callback')

        test_job_id = "12345"
        callback_function(test_job_id)

        mock_process_logic.assert_called_once_with(test_job_id, mock_redis_instance, mock_minio_instance)

    @patch('worker.consumer.sys.exit')
    @patch('worker.consumer.MinioClient')
    @patch('worker.consumer.RabbitMQConsumer')
    def test_stop_handler(self, mock_rabbitmq, mock_minio, mock_exit):
        mock_consumer_instance = mock_rabbitmq.return_value
        
        main()
        
        with patch('signal.signal') as mock_signal:
            main()
            args, kwargs = mock_signal.call_args
            stop_handler = args[1]
            
            stop_handler(signal.SIGINT, None)

            mock_consumer_instance.stop.assert_called()
            mock_exit.assert_called_once_with(0)