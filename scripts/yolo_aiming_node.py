import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64, Bool
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import os


class YoloAimingNode(Node):
    def __init__(self):
        super().__init__('yolo_aiming_node')
        script_dir = os.path.dirname(os.path.realpath(__file__))
        model_path = os.path.join(script_dir, '..', 'models', 'best.pt')
        # 1. Load your 'best' weights from the training
        self.model = YOLO(model_path)
        self.bridge = CvBridge()
        self.image_pub = self.create_publisher(Image, '/yolo/detections_image', 10)
        # 2. Subscriptions & Publications
        self.create_subscription(Image, '/wamv/sensors/cameras/front_left_camera_sensor/image_raw', self.image_callback, 10)
        self.yaw_pub = self.create_publisher(Float64, '/model/wamv/joint/ball_shooter_base_joint/cmd_pos', 10)
        self.pitch_pub = self.create_publisher(Float64, '/model/wamv/joint/ball_shooter_launcher_joint/cmd_pos', 10)
        self.fire_pub = self.create_publisher(Bool, '/wamv/shooters/ball_shooter/fire', 10)

        # Camera Intrinsics (Adjust based on your GZ camera sensor)
        self.img_width = 640
        self.img_height = 480
        self.focal_length = 500.0 

    def image_callback(self, msg):
        try:
            # 1. Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            #self.get_logger().info('IMAGE RECEIVED!')

            # 2. Run YOLO Inference
            results = self.model(cv_image, conf=0.8, verbose=False)

            # --- VISUALIZATION LOGIC START ---
            # Draw bounding boxes on the frame
            annotated_frame = results[0].plot() 
            
            # Convert the annotated frame back to a ROS Image message
            ros_img = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
            
            # Publish to the /yolo/detections_image topic
            self.image_pub.publish(ros_img)
            # --- VISUALIZATION LOGIC END ---

            # 3. Existing Aiming Logic
            for r in results:
                for box in r.boxes:
                    # Get center of the 'hole' (Class index 2 or 4 based on your YAML)
                    if int(box.cls) in [2, 4]: 
                        # Use float() to ensure compatibility with calculation
                        x_c, y_c, w, h = box.xywh[0]
                        
                        # Calculate Pixel Error from Center
                        err_x = float(x_c) - (self.img_width / 2)
                        err_y = float(y_c) - (self.img_height / 2)

                        # Convert to Radians (Mechanical Engineering Math)
                        yaw_cmd = - (err_x / self.focal_length) 
                        pitch_cmd = (err_y / self.focal_length)

                        # Publish to Gimbal
                        self.yaw_pub.publish(Float64(data=float(yaw_cmd)))
                        self.pitch_pub.publish(Float64(data=float(pitch_cmd)))

                        # Fire if centered (Threshold: 10 pixels)
                        if abs(err_x) < 10 and abs(err_y) < 10:
                            self.fire_pub.publish(Bool(data=True))
                            self.get_logger().info('TARGET LOCKED: FIRING!')
                            
        except Exception as e:
            self.get_logger().error(f'Vision Callback Failed: {e}')

def main():
    rclpy.init()
    node = YoloAimingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
