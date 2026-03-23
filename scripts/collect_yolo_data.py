import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class DataCollector(Node):
    def __init__(self):
        super().__init__('data_collector')
        # Change this if your camera topic is different
        self.subscription = self.create_subscription(Image, '/wamv/sensors/cameras/front_left_camera_sensor/image_raw', self.listener_callback, 10)
        self.bridge = CvBridge()
        self.img_count = 0
        self.save_path = 'yolo_dataset'
        if not os.path.exists(self.save_path): os.makedirs(self.save_path)
        self.get_logger().info('Data Collector started. Press Ctrl+C to stop.')

    def listener_callback(self, data):
        # Save every 30th frame (roughly once per second) to avoid duplicate data
        if self.img_count % 30 == 0:
            cv_image = self.bridge.imgmsg_to_cv2(data, 'bgr8')
            filename = os.path.join(self.save_path, f'target_{self.img_count//30:03d}.jpg')
            cv2.imwrite(filename, cv_image)
            self.get_logger().info(f'Saved: {filename}')
        self.img_count += 1

def main(args=None):
    rclpy.init(args=args)
    node = DataCollector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
