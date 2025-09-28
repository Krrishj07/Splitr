"""Small helper to compute embeddings for known images and a test image (or camera snapshot).
Run from project root like:

python app/facial_recognition/debug_embeddings.py --test-image path/to/some.jpg

Or to capture a single frame from camera and compare:

python app/facial_recognition/debug_embeddings.py --camera

This prints per-person mean embeddings and distances so you can tune MATCH_THRESHOLD.
"""
import os, glob, argparse
import numpy as np
from PIL import Image

try:
    import torch
    from facenet_pytorch import MTCNN, InceptionResnetV1
except Exception as e:
    print('Missing ML packages. Install facenet-pytorch and torch in your venv:', e)
    raise

parser = argparse.ArgumentParser()
parser.add_argument('--test-image', help='Path to a test image')
parser.add_argument('--camera', action='store_true', help='Capture a single frame from camera')
parser.add_argument('--device', default=None, help='Torch device to use (cpu/mps/cuda)')
args = parser.parse_args()

# Determine device attempts: use user-provided, otherwise prefer mps then cpu
preferred = []
if args.device:
    preferred = [args.device]
else:
    preferred = ['mps', 'cpu'] if torch.backends.mps.is_available() else ['cpu']

mtcnn = None
resnet = None
device = None
init_success = False
for dev_try in preferred:
    try:
        print('Attempting model init on device:', dev_try)
        mtcnn = MTCNN(keep_all=False, device=dev_try)
        resnet = InceptionResnetV1(pretrained='vggface2').eval().to(dev_try)
        device = dev_try
        init_success = True
        print('Models initialized on', device)
        break
    except Exception as e:
        print(f'Model init failed on {dev_try}:', e)
        mtcnn = None
        resnet = None

if not init_success:
    raise SystemExit('Failed to initialize models on attempted devices. Try --device cpu or set FORCE_TORCH_DEVICE=cpu')

known_dir = os.path.join(os.path.dirname(__file__), 'known')
people = {}
def is_image_file(path):
    return os.path.isfile(path) and os.path.splitext(path)[1].lower() in ('.jpg', '.jpeg', '.png')

for person in os.listdir(known_dir):
    person_path = os.path.join(known_dir, person)
    if not os.path.isdir(person_path):
        # skip files like .DS_Store
        print('Skipping non-directory entry in known/:', person)
        continue
    emb_list = []
    for p in glob.glob(os.path.join(person_path, '*')):
        if not is_image_file(p):
            print('Skipping non-image file:', p)
            continue
        try:
            img = Image.open(p).convert('RGB')
            face = mtcnn(img)
        except RuntimeError as e:
            # MPS adaptive pool error may appear here; try to reinit models on CPU and retry
            msg = str(e)
            print('RuntimeError during face detection:', msg)
            if 'Adaptive pool MPS' in msg or 'MPS' in msg:
                print('Retrying models on CPU due to MPS adaptive-pool limitation')
                mtcnn = MTCNN(keep_all=False, device='cpu')
                resnet = InceptionResnetV1(pretrained='vggface2').eval().to('cpu')
                device = 'cpu'
                face = mtcnn(img)
            else:
                raise

        if face is None:
            print('No face detected in', p)
            continue
        with torch.no_grad():
            if face.dim() == 3:
                inp = face.unsqueeze(0).to(device)
            else:
                inp = face.to(device)
            emb = resnet(inp).cpu().numpy()[0]
        emb_list.append(emb)
    if emb_list:
        people[person] = np.stack(emb_list)
        print(f'Loaded {len(emb_list)} images for {person}')
    else:
        print('No embeddings for person', person)

# get test embedding
if args.camera:
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise SystemExit('Camera capture failed')
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    face = mtcnn(pil)
    if face is None:
        raise SystemExit('No face detected in camera frame')
    with torch.no_grad():
        inp = face.unsqueeze(0).to(device) if face.dim()==3 else face.to(device)
        test_emb = resnet(inp).cpu().numpy()[0]
elif args.test_image:
    img = Image.open(args.test_image).convert('RGB')
    face = mtcnn(img)
    if face is None:
        raise SystemExit('No face detected in test image')
    with torch.no_grad():
        inp = face.unsqueeze(0).to(device) if face.dim()==3 else face.to(device)
        test_emb = resnet(inp).cpu().numpy()[0]
else:
    raise SystemExit('Provide --test-image or --camera')

print('\nComparing test embedding to known people:')
for person, embs in people.items():
    dists = np.linalg.norm(embs - test_emb, axis=1)
    print(person, 'min=', dists.min(), 'mean=', dists.mean())

print('\nDone')
