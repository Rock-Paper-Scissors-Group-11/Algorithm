const TARGET_SCORE = 3;
const COUNTDOWN_SECONDS = 3;
const CAPTURE_SECONDS = 5;
const RESULT_SECONDS = 2;
const HISTORY_KEY = "handrps.matches.v1";
const GESTURES = ["ROCK", "PAPER", "SCISSORS"];
const GESTURE_DETAILS = {
  ROCK: { label: "Rock", icon: new URL("./assets/icons/rock.svg", import.meta.url).href },
  PAPER: { label: "Paper", icon: new URL("./assets/icons/paper.svg", import.meta.url).href },
  SCISSORS: { label: "Scissors", icon: new URL("./assets/icons/scissors.svg", import.meta.url).href },
};
const MODEL_URL = new URL("./assets/models/hand_landmarker.task", import.meta.url).href;
const SOUND_URLS = Object.fromEntries(
  [
    ["countdown", "mp3"],
    ["win", "mp3"],
    ["lose", "mp3"],
    ["draw", "mp3"],
    ["match", "wav"],
  ].map(([name, extension]) => [
    name, new URL(`./assets/sounds/${name}.${extension}`, import.meta.url).href,
  ]),
);
const MEDIAPIPE_VERSION = "0.10.21";
const MEDIAPIPE_ROOT = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}`;
const $ = (selector) => document.querySelector(selector);

const ui = {
  pages: { play: $("#playPage"), history: $("#historyPage"), about: $("#aboutPage") },
  nav: [...document.querySelectorAll("[data-page]")],
  cameraVideo: $("#cameraVideo"),
  cameraPlaceholder: $("#cameraPlaceholder"),
  cameraStatus: $("#cameraStatus"),
  cameraDot: $("#cameraDot"),
  detectionLabel: $("#detectionLabel"),
  liveDot: $(".live-dot"),
  gestureChip: $("#gestureChip"),
  trackingBadge: $("#trackingBadge"),
  playerHint: $("#playerHint"),
  roundNumber: $("#roundNumber"),
  drawNumber: $("#drawNumber"),
  playerScore: $("#playerScore"),
  aiScore: $("#aiScore"),
  aiOrb: $("#aiOrb"),
  aiMoveLabel: $("#aiMoveLabel"),
  aiHint: $("#aiHint"),
  roundTitle: $("#roundTitle"),
  roundMessage: $("#roundMessage"),
  messageIcon: $("#messageIcon"),
  homeActions: $("#homeActions"),
  moveActions: $("#moveActions"),
  resultActions: $("#resultActions"),
  roundProgress: $("#roundProgress"),
  progressFill: $("#progressFill"),
  toast: $("#toast"),
  soundToggle: $("#soundToggle"),
  historyRows: $("#historyRows"),
  emptyHistory: $("#emptyHistory"),
};

const state = {
  phase: "home",
  mode: null,
  score: { player: 0, ai: 0, draws: 0, rounds: 0 },
  playerMove: null,
  aiMove: null,
  deadline: 0,
  captureStart: 0,
  detectionVotes: [],
  lastInferenceAt: 0,
  handLandmarker: null,
  cameraStream: null,
  cameraRunning: false,
  matches: loadHistory(),
  currentMatch: null,
  soundEnabled: true,
  lastCountdownSecond: null,
  toastTimer: null,
  audioPlayers: {},
};

function loadHistory() {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.filter((match) => match && Array.isArray(match.rounds)) : [];
  } catch (error) {
    console.warn("Could not load saved match history.", error);
    return [];
  }
}

function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(state.matches.slice(0, 100)));
    return true;
  } catch (error) {
    showToast("Could not save match history in this browser.");
    console.error("Could not save match history.", error);
    return false;
  }
}

function setPage(page) {
  Object.entries(ui.pages).forEach(([name, element]) => {
    const active = name === page;
    element.hidden = !active;
    element.classList.toggle("is-visible", active);
  });
  ui.nav.forEach((button) => {
    if (button.classList.contains("nav-link")) {
      button.classList.toggle("is-active", button.dataset.page === page);
      if (button.dataset.page === page) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    }
  });
  if (page === "history") renderHistory();
}

function showToast(message) {
  ui.toast.textContent = message;
  ui.toast.classList.add("is-visible");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => ui.toast.classList.remove("is-visible"), 5000);
}

function setCameraStatus(connected, text) {
  ui.cameraStatus.textContent = text;
  ui.cameraDot.parentElement.classList.toggle("is-connected", connected);
}

function updateScores() {
  ui.playerScore.textContent = String(state.score.player);
  ui.aiScore.textContent = String(state.score.ai);
  ui.drawNumber.textContent = String(state.score.draws);
  ui.roundNumber.textContent = String(state.score.rounds + 1);
}

function showMove(move, side) {
  const target = side === "ai" ? ui.aiOrb : ui.gestureChip;
  const details = GESTURE_DETAILS[move];
  if (side === "ai") {
    target.innerHTML = moveIconMarkup(move);
    target.classList.add("has-move");
    ui.aiMoveLabel.textContent = details.label.toUpperCase();
    ui.aiHint.textContent = "Move revealed!";
    return;
  }
  target.innerHTML = `${moveIconMarkup(move)} ${details.label}`;
  target.hidden = false;
}

function hideAiMove() {
  ui.aiOrb.innerHTML = '<span class="question-mark">?</span>';
  ui.aiOrb.classList.remove("has-move");
  ui.aiMoveLabel.textContent = "HIDDEN CHOICE";
  ui.aiHint.textContent = "The AI has picked its move.";
}

function setRoundMessage(title, message, icon = "✦") {
  ui.roundTitle.textContent = title;
  ui.roundMessage.textContent = message;
  ui.messageIcon.textContent = icon;
}

function startMatch(mode) {
  state.mode = mode;
  state.phase = "countdown";
  state.lastCountdownSecond = null;
  state.score = { player: 0, ai: 0, draws: 0, rounds: 0 };
  state.currentMatch = {
    id: `M${Date.now().toString(36).toUpperCase()}`,
    startedAt: new Date().toISOString(),
    mode,
    rounds: [],
  };
  ui.gestureChip.hidden = true;
  ui.trackingBadge.classList.remove("is-error");
  ui.trackingBadge.classList.toggle("is-detecting", mode === "camera");
  ui.trackingBadge.textContent = mode === "camera" ? "● Camera ready" : "● Manual mode";
  beginRound();
  renderGame();
}

function beginRound() {
  if (state.score.player >= TARGET_SCORE || state.score.ai >= TARGET_SCORE) {
    finishMatch();
    return;
  }
  state.phase = "countdown";
  state.playerMove = null;
  state.lastCountdownSecond = null;
  state.aiMove = GESTURES[Math.floor(Math.random() * GESTURES.length)];
  state.deadline = performance.now() + COUNTDOWN_SECONDS * 1000;
  state.detectionVotes = [];
  ui.gestureChip.hidden = true;
  hideAiMove();
  ui.liveDot.classList.toggle("is-live", state.mode === "camera");
  ui.detectionLabel.textContent = state.mode === "camera" ? "GET READY" : "MANUAL PLAY";
  ui.playerHint.textContent = state.mode === "camera"
    ? "Wait for GO, then show one clear hand gesture."
    : "Choose your move when the countdown reaches GO.";
  ui.progressFill.style.width = "0%";
  state.score.rounds = state.currentMatch.rounds.length;
  updateScores();
  renderGame();
  tick();
}

function startCapture() {
  if (state.phase !== "countdown") return;
  state.phase = "capture";
  state.captureStart = performance.now();
  state.deadline = state.captureStart + CAPTURE_SECONDS * 1000;
  ui.detectionLabel.textContent = "GO! SHOW YOUR MOVE";
  ui.playerHint.textContent = state.mode === "camera"
    ? "Hold rock, paper, or scissors clearly in the camera."
    : "Tap your move below.";
  ui.trackingBadge.textContent = state.mode === "camera" ? "● Looking for a hand" : "● Your turn";
  if (state.mode === "manual") {
    document.querySelectorAll(".move-button").forEach((button) => { button.disabled = false; });
  }
  renderGame();
  tick();
}

function classifyLandmarks(landmarks) {
  if (!landmarks || landmarks.length !== 21) return "UNKNOWN";
  const wrist = landmarks[0];
  const fingers = { index: [6, 8], middle: [10, 12], ring: [14, 16], pinky: [18, 20] };
  const states = {};
  for (const [name, [joint, tip]] of Object.entries(fingers)) {
    const distance = (point) => Math.hypot(point.x - wrist.x, point.y - wrist.y);
    const jointDistance = distance(landmarks[joint]);
    const ratio = jointDistance ? distance(landmarks[tip]) / jointDistance : 0;
    states[name] = ratio > 1.15;
  }
  const extended = Object.values(states).filter(Boolean).length;
  if (states.index && states.middle && !states.ring && !states.pinky) return "SCISSORS";
  if (extended >= 3) return "PAPER";
  if (extended === 0) return "ROCK";
  return "UNKNOWN";
}

function stableGesture(gesture) {
  state.detectionVotes.push(gesture);
  if (state.detectionVotes.length > 10) state.detectionVotes.shift();
  const counts = new Map();
  state.detectionVotes.forEach((vote) => counts.set(vote, (counts.get(vote) || 0) + 1));
  for (const move of GESTURES) {
    if ((counts.get(move) || 0) >= 7) return move;
  }
  return null;
}

function detectFrame(now) {
  if (!state.cameraRunning || !state.handLandmarker || ui.cameraVideo.readyState < 2) return;
  if (now - state.lastInferenceAt < 100) return;
  state.lastInferenceAt = now;
  try {
    const result = state.handLandmarker.detectForVideo(ui.cameraVideo, now);
    const landmarks = result.landmarks?.[0];
    if (state.phase !== "capture" || state.mode !== "camera") return;
    if (!landmarks) {
      state.detectionVotes = [];
      ui.trackingBadge.textContent = "● Looking for a hand";
      return;
    }
    const raw = classifyLandmarks(landmarks);
    const stable = stableGesture(raw);
    if (stable) {
      ui.gestureChip.hidden = false;
      ui.gestureChip.innerHTML = `${moveIconMarkup(stable)} ${GESTURE_DETAILS[stable].label}`;
      ui.playerHint.textContent = "Move recognized — locking in your round.";
      ui.trackingBadge.textContent = "● Move recognized";
      finishRound(stable);
    } else if (raw !== "UNKNOWN") {
      ui.trackingBadge.textContent = "● Stabilizing gesture";
    } else {
      ui.trackingBadge.textContent = "● Gesture unclear";
    }
  } catch (error) {
    console.error("Hand detection failed.", error);
    showToast("Hand detection stopped. You can finish with manual play or start a new match.");
    stopCamera();
    state.phase = "home";
    renderGame();
  }
}

function finishRound(move) {
  if (state.phase !== "capture") return;
  const winsAgainst = { ROCK: "SCISSORS", PAPER: "ROCK", SCISSORS: "PAPER" };
  const result = move === "UNKNOWN" ? "LOSE"
    : move === state.aiMove ? "DRAW"
      : winsAgainst[move] === state.aiMove ? "WIN" : "LOSE";
  if (result === "WIN") state.score.player += 1;
  else if (result === "LOSE") state.score.ai += 1;
  else state.score.draws += 1;

  state.phase = "result";
  state.deadline = performance.now() + RESULT_SECONDS * 1000;
  state.playerMove = move;
  showMove(state.aiMove, "ai");
  if (move !== "UNKNOWN") showMove(move, "player");
  ui.detectionLabel.textContent = move === "UNKNOWN" ? "NO CLEAR GESTURE" : "ROUND COMPLETE";
  ui.liveDot.classList.remove("is-live");
  document.querySelectorAll(".move-button").forEach((button) => { button.disabled = true; });

  const round = {
    player: move,
    computer: state.aiMove,
    result,
    score: `${state.score.player}–${state.score.ai}`,
    playedAt: new Date().toISOString(),
  };
  state.currentMatch.rounds.push(round);
  updateScores();

  if (move === "UNKNOWN") {
    setRoundMessage("AI wins this round", "No clear hand gesture was recognized before time ran out.", "!");
  } else if (result === "WIN") {
    setRoundMessage("You win this round!", `${GESTURE_DETAILS[move].label} beats ${GESTURE_DETAILS[state.aiMove].label.toLowerCase()}.`, "✓");
  } else if (result === "LOSE") {
    setRoundMessage("AI wins this round", `${GESTURE_DETAILS[state.aiMove].label} beats ${GESTURE_DETAILS[move].label.toLowerCase()}.`, "×");
  } else {
    setRoundMessage("It's a draw", "You both chose the same move. No point awarded.", "=");
  }
  playSound(result === "WIN" ? "win" : result === "LOSE" ? "lose" : "draw");
  renderGame();
}

function finishMatch() {
  if (!state.currentMatch || state.currentMatch.saved) return;
  state.currentMatch.saved = true;
  state.currentMatch.finishedAt = new Date().toISOString();
  state.currentMatch.outcome = state.score.player > state.score.ai ? "WIN" : "LOSE";
  state.matches.unshift(state.currentMatch);
  state.matches = state.matches.slice(0, 100);
  saveHistory();
  state.phase = "gameover";
  state.mode = null;
  ui.liveDot.classList.remove("is-live");
  ui.trackingBadge.classList.remove("is-detecting");
  setRoundMessage(
    state.score.player > state.score.ai ? "You won the match!" : "The AI won this match",
    `Final score: you ${state.score.player} – ${state.score.ai} AI. Start another match whenever you're ready.`,
    state.score.player > state.score.ai ? "♛" : "↻",
  );
  playSound("match");
  renderGame();
}

function tick() {
  const now = performance.now();
  if (state.phase === "countdown") {
    const remaining = Math.max(0, state.deadline - now);
    const seconds = Math.ceil(remaining / 1000);
    if (seconds !== state.lastCountdownSecond) {
      if (seconds > 0 && state.lastCountdownSecond === null) playSound("countdown");
      state.lastCountdownSecond = seconds;
    }
    setRoundMessage(seconds ? `Get ready… ${seconds}` : "GO!", seconds ? "Show your move when the countdown ends." : "Show your move now!", seconds ? "⌛" : "GO");
    ui.detectionLabel.textContent = seconds ? `STARTING IN ${seconds}` : "GO! SHOW YOUR MOVE";
    if (remaining <= 0) startCapture();
  } else if (state.phase === "capture") {
    const elapsed = now - state.captureStart;
    const progress = Math.min(100, (elapsed / (CAPTURE_SECONDS * 1000)) * 100);
    ui.progressFill.style.width = `${progress}%`;
    if (now >= state.deadline) finishRound("UNKNOWN");
  } else if (state.phase === "result" && now >= state.deadline) {
    if (state.score.player >= TARGET_SCORE || state.score.ai >= TARGET_SCORE) finishMatch();
    else beginRound();
  }
}

function renderGame() {
  const active = ["countdown", "capture", "result"].includes(state.phase);
  const ended = state.phase === "gameover";
  ui.homeActions.hidden = active || ended;
  ui.moveActions.hidden = !active || state.mode !== "manual" || state.phase !== "capture";
  ui.resultActions.hidden = !ended;
  ui.roundProgress.hidden = state.phase !== "capture";
  ui.aiOrb.classList.toggle("has-move", state.phase === "result" || ended);
  updateScores();
}

async function ensureCameraAndModel() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Camera access is unavailable here. Use HTTPS or localhost, or choose Play with buttons.");
  }
  if (!state.cameraStream) {
    state.cameraStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
    });
    ui.cameraVideo.srcObject = state.cameraStream;
    await ui.cameraVideo.play();
    ui.cameraPlaceholder.hidden = true;
    state.cameraRunning = true;
    setCameraStatus(true, "Camera connected");
  }
  if (!state.handLandmarker) {
    ui.playerHint.textContent = "Loading hand tracking model (first load may take a moment)…";
    ui.trackingBadge.textContent = "● Loading model";
    const { HandLandmarker, FilesetResolver } = await import(`${MEDIAPIPE_ROOT}/vision_bundle.mjs`);
    const vision = await FilesetResolver.forVisionTasks(`${MEDIAPIPE_ROOT}/wasm`);
    state.handLandmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: MODEL_URL },
      runningMode: "VIDEO",
      numHands: 1,
      minHandDetectionConfidence: 0.65,
      minHandPresenceConfidence: 0.55,
      minTrackingConfidence: 0.55,
    });
  }
}

async function startCameraMatch() {
  ui.cameraStartButton.disabled = true;
  ui.cameraStartButton.textContent = "Connecting camera…";
  try {
    await ensureCameraAndModel();
    startMatch("camera");
  } catch (error) {
    console.error("Could not start camera match.", error);
    setCameraStatus(false, "Camera unavailable");
    ui.trackingBadge.classList.add("is-error");
    ui.trackingBadge.textContent = "● Camera unavailable";
    ui.playerHint.textContent = error.message || "Could not start camera play.";
    showToast(error.message || "Could not start the camera. Try playing with buttons.");
    if (state.cameraStream && !state.handLandmarker) stopCamera();
  } finally {
    ui.cameraStartButton.disabled = false;
    ui.cameraStartButton.innerHTML = "<span>◎</span> Start camera match";
  }
}

function stopCamera() {
  state.cameraRunning = false;
  if (state.cameraStream) state.cameraStream.getTracks().forEach((track) => track.stop());
  state.cameraStream = null;
  ui.cameraVideo.srcObject = null;
  ui.cameraPlaceholder.hidden = false;
  ui.detectionLabel.textContent = "CAMERA NOT STARTED";
  ui.liveDot.classList.remove("is-live");
  setCameraStatus(false, "Camera off");
  if (state.handLandmarker) {
    state.handLandmarker.close();
    state.handLandmarker = null;
  }
}

function moveIconMarkup(move) {
  const details = GESTURE_DETAILS[move];
  return `<img class="move-icon" src="${details.icon}" alt="${details.label}">`;
}

function playSound(name) {
  if (!state.soundEnabled) return;
  const url = SOUND_URLS[name];
  if (!url) throw new Error(`Unknown sound effect: ${name}`);
  const player = state.audioPlayers[name] || (state.audioPlayers[name] = new Audio(url));
  player.currentTime = 0;
  player.play().catch((error) => console.warn(`Could not play the ${name} sound effect.`, error));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function renderHistory() {
  const rounds = state.matches.flatMap((match) => match.rounds.map((round, index) => ({
    ...round,
    matchId: match.id,
    matchDate: match.startedAt,
    roundIndex: index + 1,
    mode: match.mode,
  })));
  const wins = state.matches.filter((match) => match.outcome === "WIN").length;
  const losses = state.matches.filter((match) => match.outcome === "LOSE").length;
  const totalRounds = rounds.length;
  const draws = rounds.filter((round) => round.result === "DRAW").length;
  const moveCounts = Object.fromEntries(GESTURES.map((move) => [move, 0]));
  rounds.forEach((round) => { if (moveCounts[round.player] !== undefined) moveCounts[round.player] += 1; });
  const favorite = GESTURES.reduce((best, move) => moveCounts[move] > moveCounts[best] ? move : best, GESTURES[0]);
  const favoriteCount = moveCounts[favorite];

  $("#statMatches").textContent = String(state.matches.length);
  $("#statWins").textContent = String(wins);
  $("#statWinRate").textContent = `${state.matches.length ? Math.round((wins / state.matches.length) * 100) : 0}% win rate`;
  $("#statLosses").textContent = String(losses);
  $("#statDraws").textContent = String(draws);
  $("#statFavorite").textContent = favoriteCount ? GESTURE_DETAILS[favorite].label : "—";
  $("#statFavoriteRate").textContent = favoriteCount ? `${Math.round((favoriteCount / totalRounds) * 100)}% of your moves` : "Play a match to find out";
  $("#historyCount").textContent = `${totalRounds} ${totalRounds === 1 ? "round" : "rounds"}`;
  ui.emptyHistory.hidden = rounds.length > 0;
  ui.historyRows.innerHTML = [...rounds].slice(0, 60).map((round) => {
    const detail = (move) => GESTURE_DETAILS[move]?.label || "Unclear";
    const icon = (move) => GESTURE_DETAILS[move]
      ? moveIconMarkup(move)
      : '<span aria-label="Unclear move">?</span>';
    const resultLabel = round.result === "WIN" ? "VICTORY" : round.result === "LOSE" ? "DEFEAT" : "DRAW";
    const resultClass = round.result === "WIN" ? "win" : round.result === "LOSE" ? "loss" : "draw";
    const date = new Date(round.playedAt || round.matchDate);
    return `<tr>
      <td><strong>${escapeHtml(round.matchId)}</strong> <span class="table-count">R${round.roundIndex}</span></td>
      <td>${escapeHtml(date.toLocaleString())}</td>
      <td><span class="move-tag">${icon(round.player)} ${escapeHtml(detail(round.player))}</span></td>
      <td><span class="move-tag">${icon(round.computer)} ${escapeHtml(detail(round.computer))}</span></td>
      <td><span class="result-tag ${resultClass}">${resultLabel}</span></td>
      <td><span class="final-score">${escapeHtml(round.score)}</span></td>
    </tr>`;
  }).join("");
}

function exportHistory() {
  const rows = [["Match", "Date", "Round", "Your move", "Computer move", "Result", "Score"]];
  state.matches.forEach((match) => match.rounds.forEach((round, index) => rows.push([
    match.id,
    new Date(round.playedAt || match.startedAt).toISOString(),
    String(index + 1),
    GESTURE_DETAILS[round.player]?.label || "Unclear",
    GESTURE_DETAILS[round.computer]?.label || "Unclear",
    round.result,
    round.score,
  ])));
  if (rows.length === 1) {
    showToast("There are no matches to export yet.");
    return;
  }
  const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",")).join("\r\n");
  const link = document.createElement("a");
  const downloadUrl = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  link.href = downloadUrl;
  link.download = "handrps-match-history.csv";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
}

document.querySelectorAll("[data-page]").forEach((button) => {
  button.addEventListener("click", () => setPage(button.dataset.page));
});
$("#cameraStartButton").addEventListener("click", startCameraMatch);
$("#cameraAgainButton").addEventListener("click", startCameraMatch);
$("#manualStartButton").addEventListener("click", () => startMatch("manual"));
$("#newMatchButton").addEventListener("click", () => {
  state.phase = "home";
  state.mode = null;
  state.currentMatch = null;
  state.score = { player: 0, ai: 0, draws: 0, rounds: 0 };
  ui.gestureChip.hidden = true;
  setRoundMessage("Ready when you are", "Start a camera match or play with the move buttons.");
  ui.trackingBadge.classList.remove("is-detecting");
  ui.trackingBadge.textContent = state.cameraRunning ? "● Camera ready" : "● Ready";
  renderGame();
});
document.querySelectorAll(".move-button").forEach((button) => {
  button.addEventListener("click", () => finishRound(button.dataset.move));
});
$("#soundToggle").addEventListener("click", () => {
  state.soundEnabled = !state.soundEnabled;
  $("#soundToggle").innerHTML = `<img src="assets/icons/sound-${state.soundEnabled ? "on" : "off"}.svg" alt="">`;
  $("#soundToggle").setAttribute("aria-label", state.soundEnabled ? "Turn sound off" : "Turn sound on");
  showToast(state.soundEnabled ? "Sound effects on." : "Sound effects muted.");
});
$("#exportButton").addEventListener("click", exportHistory);
$("#clearHistoryButton").addEventListener("click", () => {
  if (!state.matches.length) {
    showToast("There is no saved match history to clear.");
    return;
  }
  if (!window.confirm("Delete all match history saved in this browser?")) return;
  state.matches = [];
  saveHistory();
  renderHistory();
});

function animationLoop(now) {
  detectFrame(now);
  window.requestAnimationFrame(animationLoop);
}

setInterval(tick, 100);
setInterval(() => {
  if (!ui.pages.history.hidden) renderHistory();
}, 1000);
window.addEventListener("pagehide", stopCamera);
window.requestAnimationFrame(animationLoop);
renderGame();
renderHistory();
