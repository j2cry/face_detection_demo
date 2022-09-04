const RESIZE = params['resize']

// init websocket
serviceURL = new URL(params['service_url'])
const socket = io(serviceURL.origin, {path: serviceURL.pathname + '/socket.io'})

// add on document load listener
window.addEventListener('load', () => {
    // wait until cv is REALLY initialized
    cv.onRuntimeInitialized = function () {
        let stream, capture, taskID
        let srcFrame, dstFrame
        const video = document.getElementById("video")        
        const canvas = document.getElementById("canvas")

        const startBtn = document.getElementById("startBtn")
        startBtn.onclick = async function (ev) {
            // start/stop webcam capturing
            if (this.innerHTML == "Start") {
                this.classList.remove("btn-success")
                this.classList.add("btn-danger")
                this.innerHTML = "Stop"
                // init webcam
                stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
                video.srcObject = stream;
                video.play();
                video.onplaying = () => {
                    // start capturing
                    video.height = video.videoHeight
                    video.width = video.videoWidth
                    canvas.height = video.videoHeight
                    canvas.width = video.videoWidth
                    capture = new cv.VideoCapture(video);
                    srcFrame = new cv.Mat(video.videoHeight, video.videoWidth, cv.CV_8UC4);
                    dstFrame = new cv.Mat(video.videoHeight, video.videoWidth, cv.CV_8UC4);
                    taskID = setTimeout(captureFrame, 0)
                }
            } else {
                // stop capturing
                this.classList.remove("btn-danger")
                this.classList.add("btn-success")
                this.innerHTML = "Start"
                stream.getTracks().forEach(track => track.stop())
                video.removeAttribute('src')
                video.load()
                canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
                clearTimeout(taskID)
                srcFrame.delete()
                dstFrame.delete()
            }
        }

        function captureFrame() {
            capture.read(srcFrame);
            cv.cvtColor(srcFrame, dstFrame, cv.COLOR_RGBA2RGB)
            // resize
            if (RESIZE.length) {
                const dsize = new cv.Size(RESIZE[0], RESIZE[1]);
                cv.resize(dstFrame, dstFrame, dsize, 0, 0, cv.INTER_AREA);
            }
            // send image
            imageInfo = {
                width: RESIZE.length ? RESIZE[0] : video.width,
                height: RESIZE.length ? RESIZE[1] : video.height,
                frame: dstFrame.data
            }
            socket.emit('detect_faces', imageInfo, (detected) => {
                if (!detected) return
                // draw rects on srcFrame
                detected.forEach((box) => {
                    leftTop = new cv.Point(
                        RESIZE.length ? box[0] / RESIZE[0] * video.width  : box[0], 
                        RESIZE.length ? box[1] / RESIZE[1] * video.height : box[1])
                    rightBottom = new cv.Point(
                        RESIZE.length ? box[2] / RESIZE[0] * video.width : box[2], 
                        RESIZE.length ? box[3] / RESIZE[1] * video.height : box[3])
                    cv.rectangle(srcFrame, leftTop, rightBottom, new cv.Scalar(0, 255, 0, 125), 1)
                    cv.imshow("canvas", srcFrame)
                })
                cv.imshow("canvas", srcFrame)
                taskID = setTimeout(captureFrame, params["delay"])
        });
        }


        btn = document.getElementById("debug")
        btn.onclick = function (ev) {
            socket.emit('debug', 1, (response) => { console.log(response) })
        }
    }
});
