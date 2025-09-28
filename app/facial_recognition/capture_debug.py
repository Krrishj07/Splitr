"""Try camera capture across common backends and indices, display a live window, and save a snapshot.
Usage:
  python capture_debug.py

If the script fails to show, try running with sudo or check macOS camera permissions for the Terminal/Python.
"""
import cv2
import time

backends = []
# Try common macOS backends if available
if hasattr(cv2, 'CAP_AVFOUNDATION'):
    backends.append(cv2.CAP_AVFOUNDATION)
if hasattr(cv2, 'CAP_QT'):
    backends.append(cv2.CAP_QT)
backends.append(cv2.CAP_ANY)

indices = list(range(0,5))

found_good = False
for backend in backends:
    for idx in indices:
        print(f'Trying camera index={idx} backend={backend}')
        try:
            cap = cv2.VideoCapture(idx, backend)
        except Exception as e:
            print('  VideoCapture construction failed:', e)
            continue
        if not cap.isOpened():
            print('  cannot open')
            try:
                cap.release()
            except Exception:
                pass
            continue
        print('  opened — reading frames for 3 seconds. Press q to quit early.')
        start = time.time()
        while True:
            ret, frame = cap.read()
            if not ret:
                print('  read failed')
                break
            # compute brightness stats
            mean = frame.mean()
            std = frame.std()
            print(f'  frame stats mean={mean:.2f} std={std:.2f}')
            cv2.imshow('capture_debug', frame)
            if mean < 5 and std < 2:
                print('  frame looks mostly black/dark')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print('  user quit')
                break
            if time.time() - start > 3:
                fname = f'capture_debug_{backend}_{idx}_{int(time.time())}.jpg'
                print('  timeout — saving snapshot to', fname)
                cv2.imwrite(fname, frame)
                # mark good if not mostly black
                if mean > 10 or std > 5:
                    found_good = True
                break
        try:
            cap.release()
        except Exception:
            pass
        cv2.destroyAllWindows()
        time.sleep(0.5)
        if found_good:
            print('Good frame found — stopping further probes')
            break
    if found_good:
        break

if not found_good:
    print('No good frames captured. Check macOS Camera permissions and that no other app is using the camera.')
else:
    print('Saved at least one non-black snapshot; inspect the saved file(s).')
