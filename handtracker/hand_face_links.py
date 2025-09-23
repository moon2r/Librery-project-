# hand_face_links.py
import cv2
import mediapipe as mp
import time
import math
import webbrowser

# -------------------- Настройки --------------------
CAM_ID = 0
SHOW_FPS = True
COOLDOWN = 2.0          # защита от повторных открытий (сек)
HOLD_TIME = 1         # сколько держать pinch над кнопкой для срабатывания (сек)
PINCH_RATIO = 0.55      # чем меньше, тем “жёстче” проверка pinch (0.45..0.65 обычно норм)

# Кнопки: (title, url, (cx,cy,w,h)) — относительные координаты (0..1)
BUTTONS = [
    ("rama", "https://www.instagram.com/anarrbayev/",     (0.50, 0.75, 0.45, 0.18)),
]

# -------------------- MediaPipe init --------------------
mp_hands = mp.solutions.hands
mp_face  = mp.solutions.face_detection
mp_draw  = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5,
    model_complexity=1
)
face = mp_face.FaceDetection(min_detection_confidence=0.6)

# -------------------- Вспомогательные --------------------
def draw_buttons(img):
    h, w = img.shape[:2]
    for title, _, (cx, cy, bw, bh) in BUTTONS:
        x1 = int((cx - bw/2)*w); y1 = int((cy - bh/2)*h)
        x2 = int((cx + bw/2)*w); y2 = int((cy + bh/2)*h)
        cv2.rectangle(img, (x1,y1), (x2,y2), (80,180,255), 2)
        cv2.putText(img, title, (x1+10, y1+32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (230,230,230), 2)

def point_in_button(px, py, btn, shape):
    h, w = shape[:2]
    _, _, (cx, cy, bw, bh) = btn
    x1 = (cx - bw/2)*w; y1 = (cy - bh/2)*h
    x2 = (cx + bw/2)*w; y2 = (cy + bh/2)*h
    return x1 <= px <= x2 and y1 <= py <= y2

def norm_dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# -------------------- Основной цикл --------------------
cap = cv2.VideoCapture(CAM_ID)
if not cap.isOpened():
    raise SystemExit("Камера не открылась")

last_open = 0.0
hover_idx = None
hover_started = 0.0
prev_t = time.time()

try:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 1) Лицо — чтобы не кликало без тебя в кадре
        face_ok = False
        fr = face.process(rgb)
        if fr.detections:
            face_ok = True
            # Можно нарисовать первый бокс лица (для отладки)
            mp_draw.draw_detection(frame, fr.detections[0])

        # 2) Кнопки
        draw_buttons(frame)

        # 3) Рука/жест pinch
        hr = hands.process(rgb)
        pinch = False
        cursor_px = None

        if hr.multi_hand_landmarks:
            lm = hr.multi_hand_landmarks[0].landmark
            # кончик большого и указательного
            thumb_tip = (lm[4].x, lm[4].y)
            index_tip = (lm[8].x, lm[8].y)
            wrist     = (lm[0].x, lm[0].y)

            # адаптивная проверка pinch: сравниваем расстояние thumb-index к масштабу руки
            ref = norm_dist(wrist, (lm[9].x, lm[9].y)) or 1e-6
            ratio = norm_dist(thumb_tip, index_tip)/ref
            pinch = ratio < PINCH_RATIO

            # курсор = указательный
            idx_x = int(index_tip[0]*w); idx_y = int(index_tip[1]*h)
            cursor_px = (idx_x, idx_y)

            mp_draw.draw_landmarks(frame, hr.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
            cv2.circle(frame, (idx_x, idx_y), 9, (0,0,255) if pinch else (80,220,120), -1)
            cv2.putText(frame, f"pinch: {'YES' if pinch else 'no'}  r={ratio:.2f}",
                        (10, h-18), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220,220,220), 2)

        # 4) Логика удержания над кнопкой (hold) + cooldown
        now = time.time()
        if face_ok and pinch and cursor_px:
            # над какой кнопкой “курсор”
            over = None
            for i, btn in enumerate(BUTTONS):
                if point_in_button(cursor_px[0], cursor_px[1], btn, frame.shape):
                    over = i; break

            if over is not None:
                if hover_idx != over:
                    hover_idx = over
                    hover_started = now
                else:
                    # визуализация прогресса удержания
                    title, url, (cx, cy, bw, bh) = BUTTONS[over]
                    x1 = int((cx - bw/2)*w); y1 = int((cy - bh/2)*h)
                    x2 = int((cx + bw/2)*w); y2 = int((cy + bh/2)*h)
                    prog = min(1.0, (now - hover_started)/HOLD_TIME)
                    cv2.rectangle(frame, (x1, y2-6), (x1 + int((x2-x1)*prog), y2), (0,255,255), -1)

                    if prog >= 1.0 and (now - last_open) > COOLDOWN:
                        webbrowser.open(url, new=2)
                        last_open = now
                        hover_started = now  # сброс прогресса
                        cv2.putText(frame, f"Opening: {title}", (10, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            else:
                hover_idx = None
        else:
            hover_idx = None

        if not face_ok:
            cv2.putText(frame, "Лицо не найдено — жесты заблокированы",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,160,255), 2)

        # FPS
        if SHOW_FPS:
            cur = time.time()
            fps = 1.0/max(1e-6, cur - prev_t)
            prev_t = cur
            cv2.putText(frame, f"FPS: {int(fps)}", (w-120, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220,220,220), 2)

        cv2.imshow("Hand+Face Link Opener (MediaPipe)", frame)
        if cv2.waitKey(1) & 0xFF in (27, ord('q')):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    face.close()
