import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
import sys, select, termios, tty

class SimpleDrive(Node):
    def __init__(self):
        super().__init__('simple_drive')
        self.pub_l = self.create_publisher(Float64, '/wamv/thrusters/left/thrust', 10)
        self.pub_r = self.create_publisher(Float64, '/wamv/thrusters/right/thrust', 10)
        print("Use W/A/S/D to drive, SPACE to stop. Press CTRL+C to quit.")

    def drive(self, left, right):
        self.pub_l.publish(Float64(data=float(left)))
        self.pub_r.publish(Float64(data=float(right)))

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist: key = sys.stdin.read(1)
    else: key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = SimpleDrive()
    try:
        while True:
            key = get_key(settings)
            if key == 'w': node.drive(300, 300)
            elif key == 's': node.drive(-300, -300)
            elif key == 'a': node.drive(-200, 200)
            elif key == 'd': node.drive(200, -200)
            elif key == ' ': node.drive(0, 0)
            elif key == '\x03': break
    finally:
        node.drive(0, 0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
