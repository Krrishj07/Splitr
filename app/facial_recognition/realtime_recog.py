# realtime_recog.py
import os, glob, time, argparse, sys
import numpy as np
import cv2
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from PIL import Image

# Allow forcing device via environment variable (e.g. FORCE_TORCH_DEVICE=cpu)
env_device = os.environ.get('FORCE_TORCH_DEVICE')
if env_device:
    device = env_device
else:
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
print("device:", device)

# We'll initialize models lazily after camera opens to avoid potential conflicts
skip_models = os.environ.get('SKIP_MODELS')
mtcnn = None
resnet = None
models_initialized = False

# OpenCV Haar cascade fallback (used if MTCNN fails or returns no boxes)
haar_cascade = None
try:
    haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if haar_cascade.empty():
        haar_cascade = None
except Exception:
    haar_cascade = None

# known embeddings placeholder; will be populated after models are created
known_embeddings = np.zeros((0,512))
known_names = []
# configurable match threshold (env var MATCH_THRESHOLD)
MATCH_THRESHOLD = float(os.environ.get('MATCH_THRESHOLD', '0.8'))
# maximum frames to process (env var MAX_FRAMES). 0 means unlimited. Default 0 (unlimited for demo).
MAX_FRAMES = int(os.environ.get('MAX_FRAMES', '0'))
# headless logging: number of frames to log detailed detection/recognition info
LOG_FRAMES = int(os.environ.get('LOG_FRAMES', '0'))

# how long to keep showing camera after recognition (seconds)
RECOG_HOLD_SECS = float(os.environ.get('RECOG_HOLD_SECS', '5'))

# helper to match
def match_embedding(embedding, threshold=None):
    if threshold is None:
        threshold = MATCH_THRESHOLD
    if len(known_embeddings)==0:
        return "Unknown", None
    dists = np.linalg.norm(known_embeddings - embedding, axis=1)
    idx = np.argmin(dists)
    if dists[idx] < threshold:
        return known_names[idx], dists[idx]
    return "Unknown", dists[idx]

# open webcam or video file
parser = argparse.ArgumentParser()
parser.add_argument('--single-exit', action='store_true', help='Exit after first successful recognition and print name')
args = parser.parse_args()

video_source = os.environ.get('VIDEO_SOURCE')
video_index = os.environ.get('VIDEO_INDEX')
if video_source:
    print('Using video source file:', video_source)
    cap = cv2.VideoCapture(video_source)
else:
    idx = int(video_index) if video_index is not None else 0
    print(f'Opening camera index {idx} with AVFOUNDATION')
    cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)

    # Resolve known folder relative to this script if exists
    known_dir = os.path.join(os.path.dirname(__file__), 'known')
    if not os.path.isdir('known') and os.path.isdir(known_dir):
        # change working directory so the script can find known/ as before
        os.chdir(os.path.dirname(__file__))

frame_count = 0
recognized_name = None
recognized_time = None
while True:
    ret, frame = cap.read()
    if not ret:
        print("No frame from camera")
        break

    # stop after MAX_FRAMES if set
    if MAX_FRAMES and frame_count >= MAX_FRAMES:
        print(f'Reached MAX_FRAMES={MAX_FRAMES}, exiting')
        break

    # Initialize models after camera opens (lazy) to avoid MPS / camera interaction issues
    if not models_initialized:
        if not skip_models:
            # Try initializing models on the chosen device; if MPS-specific errors occur (adaptive pooling),
            # fall back to CPU and try again. This handles Apple Silicon MPS limitations gracefully.
            init_success = False
            attempted_devices = [device]
            if str(device) != 'cpu':
                attempted_devices.append('cpu')

            for dev_try in attempted_devices:
                try:
                    print(f'Attempting model init on device: {dev_try}')
                    mtcnn = MTCNN(keep_all=True, device=dev_try)
                    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(dev_try)
                    device = dev_try
                    # load known faces
                    known_embeddings = []
                    known_names = []
                    for person_dir in os.listdir('known'):
                        person_path = os.path.join('known', person_dir)
                        for img_path in glob.glob(os.path.join(person_path, '*')):
                            try:
                                img = Image.open(img_path).convert('RGB')
                            except Exception:
                                continue
                            face = mtcnn(img)
                            if face is None:
                                continue
                            with torch.no_grad():
                                if face.dim() == 3:
                                    inp = face.unsqueeze(0).to(device)
                                else:
                                    inp = face.to(device)
                                emb = resnet(inp)
                            known_embeddings.append(emb[0].cpu().numpy())
                            known_names.append(person_dir)
                    known_embeddings = np.stack(known_embeddings) if known_embeddings else np.zeros((0,512))
                    print(f'Models initialized on {device}. Loaded {len(known_names)} known identities, embeddings shape {known_embeddings.shape}')
                    init_success = True
                    break
                except Exception as e:
                    print(f'Model initialization failed on device {dev_try}:', e)
                    mtcnn = None
                    resnet = None

            if not init_success:
                print('\nModel initialization failed on all attempted devices.\n' \
                      'If you are on macOS/Apple Silicon, try running with CPU only:\n' \
                      '  FORCE_TORCH_DEVICE=cpu python run.py\n' \
                      'Or set the environment variable before starting the server to force CPU.\n')
        else:
            print('SKIP_MODELS set — skipping model initialization')
        models_initialized = True

    # convert to RGB PIL for MTCNN
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    boxes = None
    probs = None
    if mtcnn is not None:
        try:
            boxes, probs = mtcnn.detect(img)
        except Exception as e:
            print('mtcnn.detect error:', e)
            boxes = None

    # If MTCNN didn't return boxes and we have an OpenCV cascade, try that as a fallback
    if (boxes is None or len(boxes) == 0) and haar_cascade is not None:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60,60))
            if len(faces) > 0:
                boxes = []
                for (x, y, w, h) in faces:
                    boxes.append([x, y, x + w, y + h])
                boxes = np.array(boxes)
                # note: these boxes are coarse and unaligned; labels will be 'Unknown' unless models are present
        except Exception as e:
            print('Haar cascade detection failed:', e)

    if boxes is not None:
        for box in boxes:
            x1,y1,x2,y2 = [int(b) for b in box]
            face_crop = img.crop((x1,y1,x2,y2)).resize((160,160))
            # use mtcnn to align the cropped face (returns a tensor or None)
            if mtcnn is not None and resnet is not None:
                try:
                    aligned = mtcnn(face_crop)
                    if aligned is None:
                        label = 'No aligned face'
                    else:
                        with torch.no_grad():
                            # mtcnn(face) may return a 3D tensor (C,H,W) or 4D batched tensor (N,C,H,W)
                            if aligned.dim() == 3:
                                inp = aligned.unsqueeze(0).to(device)
                            else:
                                inp = aligned.to(device)
                            emb = resnet(inp).cpu().numpy()[0]
                        name, dist = match_embedding(emb)
                        label = f"{name} ({dist:.2f})" if dist is not None else name
                        # If we found a known person and haven't recorded anyone yet, remember them and notify caller
                        if name != 'Unknown' and recognized_name is None:
                            recognized_name = name
                            recognized_time = time.time()
                            try:
                                # print a machine-friendly result token so the caller can parse reliably
                                print(f"RECOG_RESULT:{recognized_name}", flush=True)
                            except Exception:
                                pass
                except Exception as e:
                    label = f'Model error'
                    print('Model inference error for a face:', e)
            else:
                label = 'Models skipped'
            # choose highlight for recognized faces
            try:
                is_known = (name != 'Unknown' and not label.startswith('No') and not label.startswith('Model'))
            except NameError:
                is_known = False

            if is_known:
                box_color = (255, 128, 0)  # orange-ish for known
                thickness = 3
                txt_color = (0, 0, 0)
                # draw filled rect behind text for readability
                size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                tx, ty = size
                cv2.rectangle(frame, (x1, y1 - 25), (x1 + tx + 10, y1), (255, 255, 255), -1)
            else:
                box_color = (0, 255, 0)
                thickness = 2
                txt_color = (255, 255, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, thickness)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, txt_color, 2)
            # continue drawing boxes; if we are in single-exit and a name was captured, we'll exit after a short delay
            if args.single_exit and recognized_name is not None:
                # if the hold time has passed, print and exit
                if time.time() - recognized_time >= RECOG_HOLD_SECS:
                    try:
                        # print a machine-friendly result token so the caller can parse reliably
                        print(f"RECOG_RESULT:{recognized_name}")
                    except Exception:
                        pass
                    cap.release()
                    cv2.destroyAllWindows()
                    sys.exit(0)
            # headless logging for first LOG_FRAMES frames
            if LOG_FRAMES and frame_count < LOG_FRAMES:
                print(f'frame {frame_count} box={box} label={label}')

    no_display = os.environ.get('NO_DISPLAY')
    if not no_display:
        cv2.imshow('face', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        # running headless; print a short progress indicator
        print('frame processed', flush=True)
    frame_count += 1

cap.release()
cv2.destroyAllWindows()
# If we exited naturally (no recognition) and were run in single-exit mode, emit a marker so callers know
if args.single_exit and recognized_name is None:
    try:
        print('RECOG_RESULT:Unknown')
    except Exception:
        pass