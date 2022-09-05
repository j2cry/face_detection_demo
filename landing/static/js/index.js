const RESIZE = params["resize"]

// init websocket
serviceURL = new URL(params["service_url"])
const socket = io(serviceURL.origin, {path: serviceURL.pathname + "/socket.io"})

// add on document load listener
window.addEventListener("load", () => {
    let stream
    let taskIDs = []
    let capturing = false
    const video = document.getElementById("video")        
    const cctx = document.getElementById("canvas").getContext("2d")
    const sctx = document.createElement("canvas").getContext("2d")
    // const sctx = document.getElementById("smCanvas").getContext("2d")

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
                // recalc scale
                scale = RESIZE.length ? {
                    w: RESIZE[0] > 0 ? RESIZE[0] / video.videoWidth : 1, 
                    h: RESIZE[1] > 0 ? RESIZE[1] / video.videoHeight : 1
                } : {w: 1, h: 1}
                // set DOM elements dimension
                cctx.canvas.height = video.videoHeight
                cctx.canvas.width = video.videoWidth
                sctx.scale(scale.x, scale.y)
                sctx.canvas.width = video.videoWidth * scale.w
                sctx.canvas.height = video.videoHeight * scale.h
                // init capturing
                capturing = true
                taskIDs.push(setTimeout(captureFrame, 0))
            }
        } else {
            // clear capture task list
            capturing = false
            taskIDs.forEach((tid) => { clearTimeout(tid) })
            taskIDs = []
            // clear layouts
            this.classList.remove("btn-danger")
            this.classList.add("btn-success")
            this.innerHTML = "Start"
            stream.getTracks().forEach(track => track.stop())
            video.removeAttribute("src")
            video.load()
            cctx.clearRect(0, 0, cctx.canvas.width, cctx.canvas.height)
            sctx.clearRect(0, 0, sctx.canvas.width, sctx.canvas.height)
        }
    }

    function captureFrame() {
        // scale
        sctx.drawImage(cctx.canvas, 0, 0, sctx.canvas.width, sctx.canvas.height)
        // send to API
        dataURL = sctx.canvas.toDataURL("image/png")
        image = dataURL.replace(/^data:image\/(png|jpg);base64,/, "")
        imageInfo = {frame: image, width: sctx.canvas.width, height: sctx.canvas.height}        
        socket.emit('detect_faces', imageInfo, (detected) => {
            // refresh frame
            cctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight)
            if (detected) {
                // draw rects
                cctx.beginPath()
                cctx.strokeStyle = "#00FF00"
                detected.forEach((box) => {
                    l = box[0] / scale.w
                    t = box[1] / scale.h
                    w = (box[2] - box[0]) / scale.w
                    h = (box[3] - box[1]) / scale.h
                    cctx.rect(l, t, w, h)
                })
                cctx.stroke()
            }
            if (capturing)
                taskIDs.push(setTimeout(captureFrame, params["delay"]))
            else
                cctx.clearRect(0, 0, cctx.canvas.width, cctx.canvas.height)
        });
    }


    btn = document.getElementById("debug")
    btn.onclick = function (ev) {
        socket.emit('debug', 1, (response) => { console.log(response) })
    }
});
