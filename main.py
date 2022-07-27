import pygame
from dataclasses import dataclass
import math




@dataclass
class point3D:
    x: int
    y: int
    z: int

@dataclass
class point2D:
    x: int
    y: int


def dist3d(p1:point3D, p2:point3D) -> float:
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def dist2d(p1:point2D, p2:point2D) -> float:
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)


class object2D:
    def __init__(self, points:list[point2D]) -> None:
        self.points = points

class object3D:
    def __init__(self, points:list[point3D], faces:list[list[point3D]], anchor = (0, 0, 0), triangulate=False) -> None:
        self.points = points
        self.anchor = anchor
        for p in self.points:
            p.x += self.anchor[0]
            p.y += self.anchor[1]
            p.z += self.anchor[2]
        self.faces = []
        if triangulate:
            self.triangulate_faces(faces)
        else:
            self.faces = faces

    # this has some interesting issues but ok
    def triangulate_faces(self, faces) -> None:
        for face in faces:
            if len(face) == 3:
                self.faces.append(face)
            else:
                self.faces.append(face[0:3])
                face.pop(1)
                self.triangulate_faces([face])


class camera:
    def __init__(self, pos:point3D=point3D(0, 0, 0), rot=[90, 0], fov=60) -> None:
        # pos = (x, y, z)
        # rot = (yaw, pitch)
        self.pos = pos
        self.rot = rot
        self.fov = fov

    def nodeInFov(self, node:point3D) -> bool:
        relativenode = point3D(node.x - self.pos.x, node.y - self.pos.y, node.z - self.pos.z)
        # get the difference of the angle between the node and the camera
        zangle = (math.atan2(relativenode.z, relativenode.x) - math.radians(self.rot[0]) + 360) % 360
        try:
            yangle = (math.atan2(relativenode.y, math.sqrt(relativenode.x**2 + relativenode.z**2)) - math.radians(self.rot[1]) + 360) % 360
        except ZeroDivisionError:
            yangle = self.rot[1]
        return (zangle < self.fov or zangle > 360-self.fov) and (yangle < self.fov or yangle > 360-self.fov)

    def draw(self, screen:pygame.Surface, objects:list[object3D]) -> None:
        w = screen.get_width()
        h = screen.get_height()
        objects.sort(key=lambda x: x.anchor[2])
        for obj in objects:
            for face in obj.faces:
                d = False
                for p in face:
                    if self.nodeInFov(p):
                        d = True
                        break
                if d:
                    translated_points = []
                    for p in face:
                        relative_point = point3D(p.x - self.pos.x, p.y - self.pos.y, p.z - self.pos.z)
                        # project the point to the screen
                        x = math.degrees(math.atan2(relative_point.x, relative_point.z) - math.radians(self.rot[0]))/self.fov * w + w/2
                        y = math.degrees(math.atan2(relative_point.y, math.sqrt(relative_point.x**2 + relative_point.z**2)) - math.radians(self.rot[1]))/self.fov * h + h/2
                        translated_points.append(point2D(int(x), int(y)))

                    # wireframe
#                    for p in translated_points:
#                        if p.x > 0 and p.x < w or p.y > 0 and p.y < h and dist2d(translated_points[translated_points.index(p)-1], translated_points[translated_points.index(p)]) < max(w, h):
#                            #pygame.draw.line(screen, (0, 0, 0), translated_points[0], p)
#                            pygame.draw.line(screen, (255, 255, 255), ((t:=translated_points[translated_points.index(p)-1]).x, t.y), ((t:=translated_points[translated_points.index(p)]).x, t.y))

                    # this is unshaded
                    pygame.draw.polygon(screen, (255, 255, 255), [(p.x, p.y) for p in translated_points])

                    # draw vertices
#                    for p in translated_points:
#                        pygame.draw.circle(screen, (255, 0, 0), (p.x, p.y), 2)
        pygame.display.update()



class renderer:
    def __init__(self, width:int, height:int, cameras=[camera()], background_color=(0, 0, 0)) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('3D Engine')
        self.clock = pygame.time.Clock()
        self.clock.tick(30)
        self.active_camera = 0
        self.cameras = cameras
        self.background_color = background_color

    def draw(self, objects:list[object3D]) -> None:
        self.screen.fill(self.background_color)
        try:
            self.cameras[self.active_camera].draw(self.screen, objects)
        except IndexError:
            print('No camera')
            self.active_camera = 0


def makeunitcube(objlist, anchor=(0, 0, 0), triangulate=False):
    points = [point3D(0, 0, 0), # bottom left front
              point3D(1, 0, 0), # bottom right front
              point3D(1, 1, 0), # top right front
              point3D(0, 1, 0), # top left front
              point3D(0, 0, 1), # bottom left back
              point3D(1, 0, 1), # bottom right back
              point3D(1, 1, 1), # top right back
              point3D(0, 1, 1)] # top left back

    faces = [   # front
                [points[0], points[1], points[2], points[3]],
                # back
                [points[4], points[5], points[6], points[7]],
                # bottom
                [points[0], points[1], points[5], points[4]],
                # top
                [points[2], points[3], points[7], points[6]],
                # left
                [points[0], points[3], points[7], points[4]],
                # right
                [points[1], points[2], points[6], points[5]]]

    objlist.append(object3D(points, faces, anchor, triangulate))



# works but not very well
def fibonacci_sphere(objlist, anchor=(0, 0, 0), samples=100):

    points = []
    phi = math.pi * (3. - math.sqrt(5.))  # golden angle in radians

    for i in range(samples):
        y = 1 - (i / float(samples - 1)) * 2  # y goes from 1 to -1
        radius = math.sqrt(1 - y * y)  # radius at y

        theta = phi * i  # golden angle increment

        x = math.cos(theta) * radius
        z = math.sin(theta) * radius

        points.append(point3D(x, y, z))

    faces = []
    # does not work well
    # triangulate the sphere
    for p in points:
        points.sort(key=lambda x: dist3d(p, x))
        nearest = [*filter(lambda x: dist3d(p, x) < dist3d(p, points[0])+.4, points)]
        for n in nearest:
            faces.append([p, n, points[nearest.index(n)+1]])

    objlist.append(object3D(points, faces, anchor))



if __name__ == '__main__':
    objects = []

    # cube :)
    makeunitcube(objects, (5, 2, 0), True)
    makeunitcube(objects, (6, 0, 2), True)
    makeunitcube(objects, (7, -1, 0), True)
    makeunitcube(objects, (8, -1, 2), True)

    # fibonacci sphere
    # fibonacci_sphere(objects, (10, 1, 3), 100)

    cam = camera()
    r = renderer(800, 600, [cam])

    while True:
        # pygame get events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit()
                if event.key == pygame.K_LEFT:
                    cam.rot[0] -= 1
                    print(cam.rot[0])
                if event.key == pygame.K_RIGHT:
                    cam.rot[0] += 1
                    print(cam.rot[0])
                if event.key == pygame.K_UP:
                    cam.rot[1] -= 1
                    print(cam.rot[1])
                if event.key == pygame.K_DOWN:
                    cam.rot[1] += 1
                    print(cam.rot[1])
                if event.key == pygame.K_q:
                    cam.pos.x += 1
                    print(cam.pos.x)
                if event.key == pygame.K_a:
                    cam.pos.x -= 1
                    print(cam.pos.x)
                if event.key == pygame.K_w:
                    cam.pos.y -= 1
                    print(cam.pos.y)
                if event.key == pygame.K_s:
                    cam.pos.y += 1
                    print(cam.pos.y)
                if event.key == pygame.K_e:
                    cam.pos.z += 1
                    print(cam.pos.z)
                if event.key == pygame.K_d:
                    cam.pos.z -= 1
                    print(cam.pos.z)
                if event.key == pygame.K_1:
                    r.active_camera = 0
                    print(r.active_camera)
                if event.key == pygame.K_2:
                    r.active_camera = 1
                    print(r.active_camera)
                if event.key == pygame.K_3:
                    r.active_camera = 2
                    print(r.active_camera)
                if event.key == pygame.K_4:
                    r.active_camera = 3
                    print(r.active_camera)
                if event.key == pygame.K_5:
                    r.active_camera = 4
                    print(r.active_camera)
                if event.key == pygame.K_6:
                    r.active_camera = 5
                    print(r.active_camera)
                if event.key == pygame.K_7:
                    r.active_camera = 6
                    print(r.active_camera)
                if event.key == pygame.K_8:
                    r.active_camera = 7
                    print(r.active_camera)
                if event.key == pygame.K_9:
                    r.active_camera = 8
                    print(r.active_camera)
                if event.key == pygame.K_0:
                    r.active_camera = 9
                    print(r.active_camera)
                if event.key == pygame.K_z:
                    cam.fov += 10
                    print(cam.fov)
                if event.key == pygame.K_x:
                    cam.fov -= 10
                    print(cam.fov)

        r.draw(objects)