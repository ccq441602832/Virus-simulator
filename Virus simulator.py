from math import sqrt
from enum import Enum, unique
import multiprocessing as mp
import random
import math
import pygame
import time

@unique
class Color(Enum):
    # 颜色
    GREEN = (0, 255, 0)  # 绿色表示正常
    YELLOW = (200, 200, 0)  # 黄色表示感染，但在潜伏期
    ORANGE = (150, 150, 0)  # 橙色表示感染并发病
    RED = (255, 0, 0)  # 红色表示超级传播者
    BLUE = (0, 0, 255)  # 蓝色表示治愈
    BLACK = (0, 0, 0)  # 黑色表示死亡
    GRAY = (225, 225, 225)
    WHITE = (255, 255, 255)

class People(object):
    '''
    人群
    在图像中表示为一个个小点
    不同颜色表示不同状态的人群
    '''
    def __init__(self, x, y, sx, sy, move_T, status = 0,
                 color = Color.GREEN.value, super_spreader = 0):
        self.x = x
        self.y = y
        self.sx = sx # x轴速度
        self.sy = sy # y轴速度
        self.status = status # 状态
        self.color = color # 颜色
        self.move_T = move_T # 活动周期
        self.super_spreader = super_spreader # 超级传播者，0为否，1为是
        self.incubation_period = random.randint(24, 36) + \
            random.randint(24, 36) + random.randint(24, 36)  # 患病之后的潜伏期
        self.infected_time = -1     # 感染时间。初始化时感染时间为-1
        # self.spread_time = random.randint()

        # 0 - 正常(GREEN)
        # 1 - 潜伏期(ORANGE)， 2 - 发病(RED)
        # 3 - 治愈(BLUE)， 4 - 死亡(BLACK)
        # 受感染的超级传播者(RED)
    def move(self, screen, time):
        # 在两点之间往返移动
        self.x += self.sx
        self.y += self.sy

        if round(time * 10) % self.move_T == 0:
            self.sx = -self.sx
            self.sy = -self.sy

    def infect(self, other, current_time):
        # 感染
        # 感染判定 距离为5时有2%概率感染，超级传播者、发病状态会影响传播概率
        judge = random.randint(1, 100) * (self.super_spreader + 1) + (self.status - 1) * 10
        if self != other:
            dx, dy = self.x - other.x, self.y - other.y
            distance = dx ** 2 + dy ** 2
            if distance < 25 and judge >= 98:
                other.status = 1
                other.infected_time = current_time    # 将other对象的感染时间确定
                global infected
                infected += 1

    def virus_attack(self, current_time):
        if current_time - self.infected_time == self.incubation_period:
            self.status = 2 # 如果过了潜伏期，状态改为2
            global attacked
            attacked += 1

    def draw(self, screen):
        # 绘制点
        radius = 2
        if self.status == 0:
            self.color = Color.GREEN.value
        elif self.status == 1:
            self.color = Color.ORANGE.value
        elif self.status == 2:
            self.color = Color.RED.value
            # radius = 2
        elif self.status == 3:
            self.color = Color.BLUE.value
        pygame.draw.circle(screen, self.color, (self.x, self.y), radius, 0)

# 以下为固定方法
def get_zone(side_length, screen_size):
    '''
    将屏幕分成若干个区域
    side_length - int, 小区域的边长
    screen_size - set, 2个元素, 屏幕尺寸
    返回:zone_dic - dic, key - zone_00_00, value = [(71, 71)]
    '''
    # 设定区域范围
    x_min = 52
    x_max = screen_size[0] - 300 + 48
    y_min = 52
    y_max = screen_size[1] - 100 + 48

    # 设定分区变长
    a = side_length

    point_center = []
    # 设定分区中心
    start_x = int(x_min - 1 + a / 2)
    start_y = int(y_min - 1 + a / 2)
    while start_x - 1 + a / 2 <= x_max:
        while start_y - 1 + a / 2 <= y_max:
            point_center.append((int(start_x), int(start_y)))
            start_y += a - 6
        start_x += a - 6
        start_y = int(y_min - 1 + a / 2)
        # 6为最大传染半径5 + 1

    x_list = list(set(i[0] for i in point_center))
    y_list = list(set(i[1] for i in point_center))
    x_list.sort()
    y_list.sort()
    # 创建各分区容器
    zone_dic = {}
    for i in range(len(x_list)):
        for j in range(len(y_list)):
            name = 'zone_' + str(i).zfill(2) + '_' + str(j).zfill(2)
            zone_dic[name] = [(x_list[i], y_list[j])]

    # print(zone_dic)  # 测试代码
    return zone_dic, x_list, y_list

def put_points(people, zone_dic, x_list, y_list):
    '''
    根据分区，将点分类到各个分区
    people - 装人的容器
    zone_dic - get_zone函数返回的包涵分区信息的字典
    x_list - get_zone函数返回的包涵分区x中心坐标的list
    y_list - get_zone函数返回的包涵分区y中心坐标的list
    由于分区为方块分区
    因此判定点在分区内的依据为：
    person.x + person.y - cx - cy <= 40
    '''
    for person in people:       # 遍历people容器中的每一个元素
        for i in range(len(x_list)):    # 检查x轴坐标
            if person.x - x_list[i] < 20 and person.x - x_list[i] > -20:    # 如果绝对值小于20
                for j in range(len(y_list)):        # 进行y轴坐标判断
                    if person.y - y_list[j] < 20 and person.y - y_list[j] > - 20:
                        name = 'zone_' + str(i).zfill(2) + '_' + str(j).zfill(2)
                        zone_dic[name].append(person)   # 将person放入该区

                '''判定y条件'''
                pass
            else:   # 如果绝对值大于20 跳过后续判断
                continue
    return zone_dic

# 主函数
def main():
    global infected, attacked
    infected = 50
    attacked = 0
    # start_infect - 起始感染人数
    start_infect = 50  # 测试用参数

    infected = start_infect

    # 定义用来装所有人的容器
    people = []
    # 用for循环创建对象
    count_infect = 0
    screen_size = (1080, 640)
    person_number = 8000
    for i in range(person_number):
        while True:
            sx = random.randint(-3, 3)
            sy = random.randint(-3, 3)
            if sx == 0 and sy == 0:
                continue
            else:
                break
        x = random.randint(100, screen_size[0] - 300)
        y = random.randint(100, screen_size[1] - 100)
        move_T = random.randint(2, 16)
        name = 'people' + str(i)
        locals()[name] = People(x, y, sx, sy, move_T = move_T)
        people.append(locals()[name])

    # 选定初始感染人数
    infect_list = random.sample(range(0, person_number), start_infect)
    for i in infect_list:
        name = 'people' + str(i)
        locals()[name].status = 1
        locals()[name].infected_time = 0
    # print(people)
    # 检查代码，检查初始感染者的感染时间和潜伏期
    # for i in infect_list:
    #     name = 'people' + str(i)
    #     print(locals()[name].infected_time, locals()[name].incubation_period, sep = '\t', end = '\n')

    # 选定超级传播者
    # 超级传播者 - 感染他人几率为普通传播者的3倍
    super_spreader_list = random.sample(range(0, person_number), 10)
    for i in super_spreader_list:
        name = 'people' + str(i)
        locals()[name].super_spreader = 2


    # 初始化导入的pygame中的模块
    pygame.init()
    # 设置窗口尺寸
    screen = pygame.display.set_mode(screen_size)
    # 设置标题
    pygame.display.set_caption('病毒模拟器')
    # 运行状态参数
    running = True  # 设定运行状态
    day = 0         # 时间 - 日
    time = 0        # 时间 - 小时
    total_time = 0  # 小时计数，不会归0

    # 主循环
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill(Color.GRAY.value)
        # 计时写字
        my_font = pygame.font.SysFont('arial', 16)
        text_time = 'Day:%s, Time: %s'%(day, math.floor(time))
        text_surface = my_font.render(text_time, True, Color.BLACK.value)
        screen.blit(text_surface, (20, 20))

        # 感染计数写字
        text_infected = 'Infected: %s'%infected
        text_surface2 = my_font.render(text_infected, True, Color.BLACK.value)
        screen.blit(text_surface2, (screen_size[0] - 200, screen_size[1] - 60))

        # 发病计数写字
        text_attacked = 'Attacked: %s'%attacked
        text_surface3 = my_font.render(text_attacked, True, Color.BLACK.value)
        screen.blit(text_surface3, (screen_size[0] - 100, screen_size[1] - 60))

        # 绘制人（点）
        for person in people:
            if person.status != 4:
                person.draw(screen)

        # 绘制隔离区
        point_lt = (screen_size[0] - 200, 60)   # 左上角点坐标
        rect_screen_size = (160, screen_size[1] - 120)  # 宽度和高度
        pygame.draw.rect(screen, Color.WHITE.value, (point_lt, rect_screen_size), 3)
        pygame.display.flip()

        # 100毫秒刷新一次
        pygame.time.delay(500)
        time = round((time + 1), 1)
        total_time = round((total_time + 1), 1)
        # print(total_time)
        if time == 24:
            day += 1
            time = 0

        for person in people:
            person.move(screen, total_time) # 移动点
            if person.status == 1:
                person.virus_attack(total_time) # 检查是否发病

        # 对点进行分区、传播判定
        zone_dic, x_list, y_list = get_zone(40, screen_size)
        zone_result = put_points(people, zone_dic, x_list, y_list)
        for zone in zone_result.values():
            people_list = zone[1:]
            for person in people_list:
                for other in people_list:
                    if(person.status == 1 or person.status == 2)\
                        and other.status == 0 \
                        and total_time - person.infected_time >= person.incubation_period - 48:
                        # 设定为 自身状态为1（感染）或2（发病），对方状态为0，且发病前48小时
                        person.infect(other, total_time)
            # print(zone_dic)

if __name__ == '__main__':
    main()
