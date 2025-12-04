import pygame
import serial
import winsound
import math

pygame.init()

size = 60
width = size*16
height = size*9
screen = pygame.display.set_mode((width, height))

text = []
for i in range(16) :
    text.append(pygame.font.SysFont("Segoe UI Black", int(size*0.1*(i+1))))

fps = 60
clock = pygame.time.Clock()

port = 'COM6'
baud = 9600

arduino = serial.Serial(port, baud, timeout=1)
# time.sleep(2)  # 아두이노 리셋 대기

print("아두이노 연결 완료!")

def get_pitch(data):
    ax, ay, az = map(float, data.split(','))
    return math.degrees(math.atan2(-ax, math.sqrt(ay**2+az**2)))

pitch1 = 0
pitch2 = 0
offset1 = 0
offset2 = 0
period = 6
time = [0, 5]
d_range = 5
degree = [0, 0]

# [추가] 자세 경고를 위한 설정값 변수들
WARNING_ANGLE_B = 15    # [수정] B 센서 임계값
WARNING_ANGLE_C = 15    # [추가] C 센서 임계값
WARNING_DELAY = 3000    # 3000ms (3초) 이상 유지되면 알림 울림
warning_timer = 0       # 나쁜 자세 유지 시간 측정용
is_warning = False      # 현재 경고 상태인지 플래그
DELAY_UNIT = 500

def include(pos, min, max) :
    ee = True
    for i in range(len(pos)) :
        ee = ee and min[i] <= pos[i] and pos[i] < max[i]
    return ee

run = True
while run:
    dt = clock.tick(fps)
    for event in pygame.event.get() :
        if event.type == pygame.QUIT :
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN :
            mousepos = pygame.mouse.get_pos()
            if include(mousepos, [size*7.5, size*8.2], [size*8.5, size*8.8]) :
                offset1 = pitch1
                offset2 = pitch2
                # [추가] 초기화 버튼 누르면 경고 타이머도 리셋
                warning_timer = 0
                is_warning = False
            
            # [수정] 설정 버튼 클릭 감지 (버튼 6개: Degree B, Degree C, Time)
            for i in range(6): # [수정] range(4) -> range(6)으로 변경하여 3번째 줄 추가
                # 버튼의 중심 좌표 계산
                btn_x = size * (0.3 + 2 * (i % 2))
                btn_y = size * (1 + i // 2)
                
                # 마우스가 버튼 근처를 클릭했는지 확인
                if abs(mousepos[0] - btn_x) < size * 0.5 and abs(mousepos[1] - btn_y) < size * 0.5:
                    if i == 0: # Degree B 감소 (-)
                        WARNING_ANGLE_B = max(5, WARNING_ANGLE_B - 1)
                    elif i == 1: # Degree B 증가 (+)
                        WARNING_ANGLE_B += 1
                    
                    elif i == 2: # Degree C 감소 (-) [추가]
                        WARNING_ANGLE_C = max(5, WARNING_ANGLE_C - 1)
                    elif i == 3: # Degree C 증가 (+) [추가]
                        WARNING_ANGLE_C += 1

                    elif i == 4: # Time 감소 (-) [수정] 인덱스 변경 (기존 2->4)
                        WARNING_DELAY = max(DELAY_UNIT, WARNING_DELAY - DELAY_UNIT)
                    elif i == 5: # Time 증가 (+) [수정] 인덱스 변경 (기존 3->5)
                        WARNING_DELAY += DELAY_UNIT
    
    if arduino.in_waiting > 0:
        data = arduino.readline().decode().strip()
        pitch1, pitch2, = map(get_pitch, data.split('|'))
        
    degree = [pitch2 - offset2, pitch1 - offset1]
    l = [1, 2.5]


    # [수정] 경고 로직: B와 C 각각 설정된 각도와 비교
    # degree[0]은 B, degree[1]은 C에 해당함
    if abs(degree[0]) > WARNING_ANGLE_B or abs(degree[1]) > WARNING_ANGLE_C:
        warning_timer += dt  # 나쁜 자세라면 시간을 누적
    else:
        warning_timer = 0    # 자세가 돌아오면 타이머 초기화
        is_warning = False

    if warning_timer > WARNING_DELAY:
        is_warning = True
        if (warning_timer - WARNING_DELAY) % 750 < dt:
            winsound.Beep(1000, 100)


    # image
    screen.fill((0, 0, 0))
    if is_warning:
        screen.fill((100,0,0))
    for i in range(2) :
        image = text[2].render(f"{chr(66 + i)}", True, (255, 255, 255))
        screen.blit(image, (size*15 - image.get_rect().size[0]/2, size*(2.5 + 1.5*i) - image.get_rect().size[1]/2))
        image = text[2].render(f"{round(degree[i], 2)}", True, (255, 255, 255))
        screen.blit(image, (size*15 - image.get_rect().size[0]/2, size*(3 + 1.5*i) - image.get_rect().size[1]/2))
    image = pygame.Surface((size*2, size*0.1))
    image.fill((255, 255, 255))
    screen.blit(image, (size*7, size*8))
    image = pygame.Surface((size*0.2, size*l[1]), pygame.SRCALPHA)
    image.fill((255, 255, 255))
    image2 = pygame.transform.rotate(image, (degree[1]))
    screen.blit(image2, (size*8 - size*l[1]*max(math.sin(degree[1]*math.pi/180), 0)
                        , size*8 - size*l[1]*max(math.cos(degree[1]*math.pi/180), 0)))
    
    image = pygame.Surface((size*0.2, size*l[0]), pygame.SRCALPHA)
    image.fill((255, 255, 255))
    image2 = pygame.transform.rotate(image, (degree[0]))
    screen.blit(image2, (size*8 - size*l[1]*math.sin(degree[1]*math.pi/180)\
                              - size*l[0]*max(math.sin((degree[0])*math.pi/180), 0)
                        , size*8 - size*l[1]*math.cos(degree[1]*math.pi/180)\
                                  - size*l[0]*max(math.cos((degree[0])*math.pi/180), 0)))
    
    pygame.draw.circle(screen, (255, 255, 255), (size*8 - size*l[1]*math.sin(degree[1]*math.pi/180)\
                            - size*l[0]*math.sin((degree[0])*math.pi/180)
                        , size*8 - size*l[1]*math.cos(degree[1]*math.pi/180)\
                            - size*l[0]*math.cos((degree[0])*math.pi/180)), size*0.5)
    image = pygame.Surface((size, size*0.6))
    image.fill((127, 108, 0))
    screen.blit(image, (size*7.5, size*8.2))

    # [수정] 설정 UI 그리기 (3줄로 확장: B, C, Time)
    for i in range(6) : # [수정] range(4) -> range(6)
        image = text[2].render(f"{["-", "+"][i%2]}", True, (255*(i%2), 0, 255*((i+1)%2)))
        screen.blit(image, (size*(0.3 + 2*(i%2)) - image.get_rect().size[0]/2
                            , size*(1 + i//2) - image.get_rect().size[1]/2))
        
        # [수정] 값 표시 로직 (B, C, Time 분기)
        if i % 2 == 0:
            if i == 0: # 첫 번째 줄: Degree B
                val_text = f"{WARNING_ANGLE_B}"
            elif i == 2: # 두 번째 줄: Degree C [추가]
                val_text = f"{WARNING_ANGLE_C}"
            else:      # 세 번째 줄: Time (i==4) [수정]
                val_text = f"{WARNING_DELAY / 1000}s"
            
            val_image = text[2].render(val_text, True, (255, 255, 0))
            screen.blit(val_image, (size*1.3 - val_image.get_width()/2, 
                                    size*(1 + i//2) - val_image.get_height()/2))
            
    # [수정] 라벨 텍스트 그리기 (B, C, Time)
    labels = ["Degree B", "Degree C", "Time"] # [추가] 라벨 리스트 생성
    for i, label in enumerate(labels):
        image = text[2].render(label, True, (255, 255, 255))
        # Y 위치: 0.5, 1.5, 2.5 순서로 배치
        screen.blit(image, (size*0.1, size*(0.5 + i) - image.get_rect().size[1]/2))

    if is_warning:
        msg = text[3].render("!! BAD POSTURE !!", True, (255, 50, 50))
        screen.blit(msg, (width/2 - msg.get_width()/2, 50))


    pygame.display.flip()

pygame.quit()

    

    
