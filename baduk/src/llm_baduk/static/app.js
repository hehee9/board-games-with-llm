/**
 * @file LLM Baduk 브라우저 작업대
 * @description 서버 스냅샷을 표시하고 대국 모드에 맞는 화면과 행동을 제공합니다.
 */

const FILES = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"];
const STAR_POINTS = {
  9: [3, 5, 7],
  13: [4, 7, 10],
  19: [4, 10, 16],
};

const i18n = window.LlmBadukI18n;

const initialSnapshot = {
  event: "setup",
  game_id: null,
  revision: 0,
  status: "setup",
  status_reason: "no_game",
  game_mode: null,
  players: {},
  human_color: null,
  llm_color: null,
  turn: null,
  to_play: null,
  board_size: 19,
  komi: 6.5,
  stones: {},
  legal_moves: [],
  captures: { black: 0, white: 0 },
  consecutive_passes: 0,
  move_history: [],
  last_move: null,
  takeback: null,
  resigned_by: null,
  result: null,
  score: null,
};

const ui = {
  snapshot: initialSnapshot,
  setupOpen: true,
  setupColor: "black",
  setupSize: 19,
  setupMode: "human_vs_llm",
  setupReturnFocus: null,
  requestPending: false,
  actionDialogMode: null,
  selectedPoint: null,
  scoreMode: null,
  connection: "connecting",
  error: null,
};

const elements = {
  appShell: document.querySelector("#app-shell"),
  topbar: document.querySelector(".topbar"),
  workspace: document.querySelector(".workspace"),
  boardGridShell: document.querySelector("#board-grid-shell"),
  rankGutter: document.querySelector("#rank-gutter"),
  board: document.querySelector("#baduk-board"),
  fileGutter: document.querySelector("#file-gutter"),
  boardCaption: document.querySelector("#board-caption"),
  boardStatus: document.querySelector("#board-status"),
  statusDot: document.querySelector("#status-dot"),
  revisionLabel: document.querySelector("#revision-label"),
  matchId: document.querySelector("#match-id"),
  clockFace: document.querySelector("#clock-face"),
  clockLabel: document.querySelector("#clock-label"),
  clockValue: document.querySelector("#clock-value"),
  clockDetail: document.querySelector("#clock-detail"),
  participantStrip: document.querySelector("#participant-strip"),
  liveIndicator: document.querySelector("#live-indicator"),
  lastMoveValue: document.querySelector("#last-move-value"),
  lastMoveMeta: document.querySelector("#last-move-meta"),
  moveList: document.querySelector("#move-list"),
  moveCount: document.querySelector("#move-count"),
  emptyHistory: document.querySelector("#empty-history"),
  connectionValue: document.querySelector("#connection-value"),
  errorCopy: document.querySelector("#error-copy"),
  setupLayer: document.querySelector("#setup-layer"),
  setupError: document.querySelector("#setup-error"),
  setupStartButton: document.querySelector("#setup-start-button"),
  modeButtons: document.querySelectorAll(".mode-choice [data-mode]"),
  humanColorFields: document.querySelector("#human-color-fields"),
  cliNameFields: document.querySelector("#cli-name-fields"),
  blackName: document.querySelector("#black-name"),
  whiteName: document.querySelector("#white-name"),
  newGameButton: document.querySelector("#new-game-button"),
  takebackButton: document.querySelector("#takeback-button"),
  resignButton: document.querySelector("#resign-button"),
  passButton: document.querySelector("#pass-button"),
  scoreModeControls: document.querySelector("#score-mode-controls"),
  deadModeButton: document.querySelector("#dead-mode-button"),
  sekiModeButton: document.querySelector("#seki-mode-button"),
  scoreAcceptButton: document.querySelector("#score-accept-button"),
  scoreResumeButton: document.querySelector("#score-resume-button"),
  guideSection: document.querySelector("#guide-section"),
  guideCommands: document.querySelectorAll("[data-guide-command]"),
  guidePrompts: document.querySelectorAll("[data-guide-prompt]"),
  guideTitles: document.querySelectorAll("[data-guide-title]"),
  guideCopyButtons: document.querySelectorAll("[data-copy-kind]"),
  scoreState: document.querySelector("#score-state"),
  scoreBlackTotal: document.querySelector("#score-black-total"),
  scoreWhiteTotal: document.querySelector("#score-white-total"),
  scoreBlackTerritory: document.querySelector("#score-black-territory"),
  scoreWhiteTerritory: document.querySelector("#score-white-territory"),
  scoreKomi: document.querySelector("#score-komi"),
  scorePrisoners: document.querySelector("#score-prisoners"),
  scoreNote: document.querySelector("#score-note"),
  actionDialog: document.querySelector("#game-action-dialog"),
  actionDialogEyebrow: document.querySelector("#action-dialog-eyebrow"),
  actionDialogHeading: document.querySelector("#action-dialog-heading"),
  actionDialogDescription: document.querySelector("#action-dialog-description"),
  actionDialogError: document.querySelector("#action-dialog-error"),
  actionDialogCancel: document.querySelector("#action-dialog-cancel"),
  actionDialogReject: document.querySelector("#action-dialog-reject"),
  actionDialogAccept: document.querySelector("#action-dialog-accept"),
  actionDialogPrimary: document.querySelector("#action-dialog-primary"),
  actionDialogResign: document.querySelector("#action-dialog-resign"),
  colorButtons: document.querySelectorAll("[data-color]"),
  sizeButtons: document.querySelectorAll("[data-size]"),
  localeSelects: document.querySelectorAll("[data-locale-select]"),
};

/* =================================== 다국어 표시 =================================== */

/** @description 정적 HTML 문구와 접근성 라벨을 현재 카탈로그로 갱신합니다. */
function applyStaticCopy() {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = i18n.t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", i18n.t(element.dataset.i18nAriaLabel));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", i18n.t(element.dataset.i18nPlaceholder));
  });
  elements.localeSelects.forEach((select) => {
    select.value = i18n.getLocale();
  });
  renderGuide();
}

/** @description CLI 대 CLI 관전에 필요한 명령과 세션 프롬프트를 갱신합니다. */
function renderGuide() {
  const colors = ["black", "white"];
  elements.guideSection.hidden = !isCliMode() && !isSetupCliMode();
  colors.forEach((color) => {
    const command = [
      `baduk --color ${color} wait`,
      `baduk --color ${color} move D4`,
      `baduk --color ${color} move pass`,
      `baduk --color ${color} takeback request`,
      `baduk --color ${color} takeback accept`,
      `baduk --color ${color} takeback reject`,
      `baduk --color ${color} resign`,
      `baduk --color ${color} score dead D4 --revision N`,
      `baduk --color ${color} score seki D4 --revision N`,
      `baduk --color ${color} score accept --revision N`,
      `baduk --color ${color} score resume`,
    ].join("\n");
    const title = isCliMode() ? playerName(color) : i18n.t(color === "black" ? "player.blackDefault" : "player.whiteDefault");
    const commandElement = [...elements.guideCommands].find((element) => element.dataset.guideCommand === color);
    const promptElement = [...elements.guidePrompts].find((element) => element.dataset.guidePrompt === color);
    const titleElement = [...elements.guideTitles].find((element) => element.dataset.guideTitle === color);
    if (commandElement) commandElement.textContent = command;
    if (promptElement) {
      promptElement.textContent = `${i18n.t("guide.prompt", { color })}\n${i18n.t("guide.resetStatus", { color })}`;
    }
    if (titleElement) titleElement.textContent = title;
  });
}

/** @description 오류를 언어 변경 뒤 다시 번역할 수 있는 내부 상태로 만듭니다. */
function localizedErrorState(error, fallbackKey) {
  return error && error.i18n ? error.i18n : { key: fallbackKey, values: {} };
}

/** @description 현재 오류 상태를 선택한 언어의 문구로 표시합니다. */
function errorText() {
  if (!ui.error) {
    return "";
  }
  return i18n.t(ui.error.key, ui.error.values);
}

/** @description 색상 값을 현재 언어로 표시합니다. */
function colorName(color) {
  return i18n.t(color === "black" ? "color.black" : "color.white");
}

/** @description 현재 게임이 CLI 대 CLI 관전 모드인지 반환합니다. */
function isCliMode() {
  return ui.snapshot.game_mode === "cli_vs_cli";
}

/** @description 설정 화면에서 CLI 대 CLI 모드를 선택했는지 반환합니다. */
function isSetupCliMode() {
  return ui.setupMode === "cli_vs_cli";
}

/** @description 색에 연결된 참가자 정보를 반환합니다. */
function playerForColor(color) {
  return ui.snapshot.players[color] || {};
}

/** @description CLI 참가자의 표시 이름을 반환합니다. */
function playerName(color) {
  const player = playerForColor(color);
  return player.name || i18n.t(color === "black" ? "player.blackDefault" : "player.whiteDefault");
}

/** @description 행위자 값을 현재 언어와 게임 모드에 맞게 표시합니다. */
function actorName(actor) {
  if (isCliMode() && (actor === "black" || actor === "white")) {
    return playerName(actor);
  }
  return i18n.t(actor === "llm" ? "actor.llm" : "actor.human");
}

/** @description CLI 대 CLI 대국에서 상대 색을 반환합니다. */
function opponentColor(color) {
  return color === "black" ? "white" : "black";
}

/** @description 점 좌표를 현재 언어의 접근성 문구로 표시합니다. */
function pointName(point) {
  return i18n.t("point.name", { point });
}

/** @description 패스 수를 현재 언어의 수순 표기로 표시합니다. */
function moveName(move) {
  return move === "pass" ? i18n.t("board.pass") : move;
}

/* =================================== 서버 통신 =================================== */

/** @description JSON 응답을 확인하고 서버가 보낸 도메인 오류를 전달합니다. */
async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw i18n.serverError(payload.detail);
  }
  return payload;
}

/** @description 현재 게임 스냅샷을 처음 불러옵니다. */
async function loadState() {
  try {
    const snapshot = await requestJson("/api/state");
    applySnapshot(snapshot);
    ui.connection = "connected";
    ui.error = null;
    ui.setupOpen = snapshot.game_id === null;
    render();
  } catch (error) {
    ui.connection = "error";
    ui.error = localizedErrorState(error, "error.connect");
    render();
  }
}

/** @description SSE로 전달된 전체 스냅샷을 화면 상태에 적용합니다. */
function handleServerEvent(event) {
  const snapshot = JSON.parse(event.data);
  applySnapshot(snapshot);
  ui.connection = "connected";
  ui.error = null;
  render();
}

/* =================================== 상태와 표시 =================================== */

/** @description 새 스냅샷을 적용하고 서버 기준으로 선택 상태를 정리합니다. */
function applySnapshot(snapshot) {
  ui.snapshot = snapshot;
  if (snapshot.game_mode) {
    ui.setupMode = snapshot.game_mode;
  }
  ui.selectedPoint = null;
  if (snapshot.game_id === null) {
    ui.setupOpen = true;
    ui.scoreMode = null;
  } else if (snapshot.status !== "scoring") {
    ui.scoreMode = null;
  }
}

/** @description 사람 차례에 착점 또는 패스를 보낼 수 있는지 반환합니다. */
function canHumanMove() {
  const snapshot = ui.snapshot;
  return Boolean(snapshot.game_id)
    && snapshot.status === "active"
    && !isCliMode()
    && !isTakebackPending()
    && snapshot.turn === "human"
    && !ui.requestPending
    && ui.connection === "connected";
}

/** @description 현재 스냅샷에 대기 중인 무르기 요청이 있는지 반환합니다. */
function isTakebackPending() {
  return ui.snapshot.takeback?.state === "pending";
}

/** @description 사람의 무르기 요청이 가능한지 반환합니다. */
function canRequestTakeback() {
  const snapshot = ui.snapshot;
  return Boolean(snapshot.game_id)
    && snapshot.status === "active"
    && !isCliMode()
    && !isTakebackPending()
    && snapshot.move_history.some((move) => move.actor === "human")
    && !ui.requestPending
    && ui.connection === "connected";
}

/** @description 수순에서 무르기 요청 설명에 필요한 대상과 범위를 계산합니다. */
function takebackPreview() {
  const history = ui.snapshot.move_history;
  const targetIndex = [...history].reverse().findIndex((move) => move.actor === "human");
  if (targetIndex < 0) {
    return null;
  }
  const index = history.length - 1 - targetIndex;
  return {
    target_ply: history[index].ply || index + 1,
    undone_plies: index === history.length - 1 ? 1 : 2,
  };
}

/** @description 진행 중이거나 계가 중인 게임을 기권할 수 있는지 반환합니다. */
function canResign() {
  return Boolean(ui.snapshot.game_id)
    && !isCliMode()
    && (ui.snapshot.status === "active" || ui.snapshot.status === "scoring")
    && !ui.requestPending
    && ui.connection === "connected";
}

/** @description 현재 계가에서 돌을 편집할 수 있는지 반환합니다. */
function canScoreEdit() {
  return Boolean(ui.snapshot.game_id)
    && ui.snapshot.status === "scoring"
    && !isCliMode()
    && Boolean(ui.scoreMode)
    && !ui.requestPending
    && ui.connection === "connected";
}

/** @description 계가 수락 버튼을 보낼 수 있는지 반환합니다. */
function canAcceptScore() {
  const score = ui.snapshot.score;
  return ui.snapshot.status === "scoring"
    && !isCliMode()
    && Boolean(score)
    && !score.accepted.human
    && !ui.requestPending
    && ui.connection === "connected";
}

/** @description 서버 상태를 바탕으로 현재 행동 안내를 만듭니다. */
function statusText() {
  const snapshot = ui.snapshot;
  if (ui.connection === "error") {
    return i18n.t("status.connectionError");
  }
  if (ui.connection === "disconnected") {
    return i18n.t("status.disconnected");
  }
  if (ui.error) {
    return i18n.t("status.requestError");
  }
  if (!snapshot.game_id || snapshot.status === "setup") {
    return i18n.t("status.setup");
  }
  if (snapshot.status === "resigned") {
    return i18n.t("status.resigned", { actor: actorName(snapshot.resigned_by) });
  }
  if (isTakebackPending()) {
    if (isCliMode()) {
      const requester = snapshot.takeback.requester;
      const responder = opponentColor(requester);
      return i18n.t("status.takebackCli", {
        requesterColor: colorName(requester),
        requesterName: playerName(requester),
        responderColor: colorName(responder),
        responderName: playerName(responder),
      });
    }
    return i18n.t(snapshot.takeback.requester === "llm" ? "status.takebackLlm" : "status.takebackHuman");
  }
  if (snapshot.status === "scoring") {
    if (isCliMode()) {
      return i18n.t("status.scoringCli", {
        black: playerName("black"),
        white: playerName("white"),
      });
    }
    return i18n.t("status.scoring");
  }
  if (snapshot.status === "finished" || snapshot.status === "draw") {
    if (isCliMode()) {
      return i18n.t(snapshot.status === "draw" ? "status.drawCli" : "status.finishedCli", {
        result: snapshot.result || "",
        black: playerName("black"),
        white: playerName("white"),
      });
    }
    return i18n.t(snapshot.status === "draw" ? "status.draw" : "status.finished", { result: snapshot.result || "" });
  }
  if (isCliMode()) {
    return i18n.t(snapshot.turn === "black" ? "status.cliBlack" : "status.cliWhite", {
      name: playerName(snapshot.turn),
    });
  }
  return i18n.t(snapshot.turn === "human" ? "status.human" : "status.llm");
}

/** @description 큰 차례 표시 면의 상태·결과·계가 안내를 갱신합니다. */
function renderClock() {
  const snapshot = ui.snapshot;
  let tone = "setup";
  let label = i18n.t("clock.setup.label");
  let value = i18n.t("clock.setup.value");
  let detail = i18n.t("clock.setup.detail");

  if (ui.connection === "error") {
    tone = "error";
    label = i18n.t("clock.error.label");
    value = i18n.t("clock.error.value");
    detail = i18n.t("clock.error.detail");
  } else if (ui.connection === "disconnected") {
    tone = "terminal";
    label = i18n.t("clock.disconnected.label");
    value = i18n.t("clock.disconnected.value");
    detail = i18n.t("clock.disconnected.detail");
  } else if (ui.error) {
    tone = "error";
    label = i18n.t("clock.requestError.label");
    value = i18n.t("clock.requestError.value");
    detail = i18n.t("clock.requestError.detail");
  } else if (snapshot.status === "resigned") {
    tone = "terminal";
    label = i18n.t("clock.resigned.label");
    value = i18n.t("clock.resigned.value");
    detail = i18n.t("clock.resigned.detail", { actor: actorName(snapshot.resigned_by) });
  } else if (isTakebackPending()) {
    tone = isCliMode() ? "llm" : snapshot.takeback.requester === "llm" ? "human" : "llm";
    label = i18n.t("clock.takeback.label");
    if (isCliMode()) {
      const requester = snapshot.takeback.requester;
      const responder = opponentColor(requester);
      value = i18n.t("clock.takeback.cliValue", { name: playerName(responder) });
      detail = i18n.t("clock.takeback.cliDetail", {
        requesterColor: colorName(requester),
        requesterName: playerName(requester),
        responderColor: colorName(responder),
        responderName: playerName(responder),
      });
    } else {
      value = i18n.t(snapshot.takeback.requester === "llm" ? "clock.takeback.incomingValue" : "clock.takeback.outgoingValue");
      detail = i18n.t(snapshot.takeback.requester === "llm" ? "clock.takeback.incomingDetail" : "clock.takeback.outgoingDetail");
    }
  } else if (snapshot.status === "scoring") {
    tone = "scoring";
    label = i18n.t("clock.scoring.label");
    if (isCliMode()) {
      value = i18n.t("clock.scoring.cliValue");
      detail = i18n.t("clock.scoring.cliDetail", {
        black: playerName("black"),
        white: playerName("white"),
      });
    } else {
      value = i18n.t("clock.scoring.value");
      detail = i18n.t("clock.scoring.detail");
    }
  } else if (snapshot.status === "finished" || snapshot.status === "draw") {
    tone = "terminal";
    label = i18n.t(snapshot.status === "draw" ? "clock.draw.label" : "clock.finished.label");
    value = snapshot.result || i18n.t("clock.terminal.value");
    detail = i18n.t(isCliMode() ? "clock.finished.cliDetail" : "clock.finished.detail", {
      black: playerName("black"),
      white: playerName("white"),
    });
  } else if (isCliMode() && (snapshot.turn === "black" || snapshot.turn === "white")) {
    tone = snapshot.turn === "black" ? "human" : "llm";
    label = i18n.t("clock.cli.label");
    value = playerName(snapshot.turn);
    detail = i18n.t("clock.cli.detail", { color: colorName(snapshot.turn) });
  } else if (snapshot.turn === "human") {
    tone = "human";
    label = i18n.t("clock.human.label");
    value = i18n.t("clock.human.value");
    detail = i18n.t("clock.human.detail", { color: colorName(snapshot.human_color) });
  } else if (snapshot.turn === "llm") {
    tone = "llm";
    label = i18n.t("clock.llm.label");
    value = i18n.t("clock.llm.value");
    detail = i18n.t("clock.llm.detail", { color: colorName(snapshot.llm_color) });
  }

  elements.clockFace.dataset.tone = tone;
  elements.clockLabel.textContent = label;
  elements.clockValue.textContent = value;
  elements.clockDetail.textContent = detail;
}

/** @description 양쪽 참가자의 색과 이름을 현재 대국 모드에 맞춰 표시합니다. */
function renderParticipants() {
  elements.participantStrip.replaceChildren();
  if (!ui.snapshot.game_id || !isCliMode()) {
    elements.participantStrip.hidden = true;
    return;
  }
  elements.participantStrip.hidden = false;
  ["black", "white"].forEach((color) => {
    const item = document.createElement("div");
    const colorLabel = document.createElement("span");
    const nameLabel = document.createElement("strong");
    item.className = `participant participant-${color}`;
    colorLabel.className = "participant-color";
    nameLabel.className = "participant-name";
    colorLabel.textContent = colorName(color);
    nameLabel.textContent = playerName(color);
    item.append(colorLabel, nameLabel);
    elements.participantStrip.append(item);
  });
}

/** @description 연결 상태와 오류 문구를 갱신합니다. */
function renderConnection() {
  const labels = {
    connecting: i18n.t("connection.connecting"),
    connected: i18n.t("connection.connected"),
    disconnected: i18n.t("connection.disconnected"),
    error: i18n.t("connection.error"),
  };
  elements.connectionValue.textContent = labels[ui.connection];
  elements.connectionValue.dataset.state = ui.connection;
  elements.statusDot.dataset.state = ui.connection;
  elements.liveIndicator.dataset.state = ui.connection === "connected" ? "live" : ui.connection === "error" ? "error" : "waiting";
  elements.liveIndicator.lastChild.textContent = ui.connection === "connected" ? i18n.t("live.connected") : i18n.t("live.waiting");
  elements.errorCopy.hidden = !ui.error;
  elements.errorCopy.textContent = errorText();
}

/** @description 현재 스냅샷의 계가 수치와 안내를 갱신합니다. */
function renderScore() {
  const snapshot = ui.snapshot;
  const score = snapshot.score;
  const captures = snapshot.captures || { black: 0, white: 0 };
  const territoryBlack = score ? score.territory.black.length : null;
  const territoryWhite = score ? score.territory.white.length : null;
  const prisoners = score ? score.prisoners : captures;
  const totals = score ? score.totals : null;
  elements.scoreBlackTotal.textContent = totals ? String(totals.black) : "—";
  elements.scoreWhiteTotal.textContent = totals ? String(totals.white) : "—";
  elements.scoreBlackTerritory.textContent = territoryBlack === null ? "—" : String(territoryBlack);
  elements.scoreWhiteTerritory.textContent = territoryWhite === null ? "—" : String(territoryWhite);
  elements.scoreKomi.textContent = String(snapshot.komi ?? 6.5);
  elements.scorePrisoners.textContent = `${colorName("black")} ${prisoners.black} · ${colorName("white")} ${prisoners.white}`;
  elements.scoreState.textContent = snapshot.status === "scoring"
    ? i18n.t("score.review")
    : snapshot.status === "finished" || snapshot.status === "draw" || snapshot.status === "resigned"
      ? i18n.t("score.final")
      : i18n.t("score.live");
  if (!score) {
    elements.scoreNote.textContent = i18n.t("score.waiting");
  } else if (snapshot.status === "scoring") {
    if (isCliMode()) {
      elements.scoreNote.textContent = i18n.t("score.acceptedCli", {
        black: score.accepted.black ? i18n.t("score.acceptedShort") : i18n.t("score.pendingShort"),
        white: score.accepted.white ? i18n.t("score.acceptedShort") : i18n.t("score.pendingShort"),
      });
    } else {
      elements.scoreNote.textContent = i18n.t("score.accepted", {
        human: score.accepted.human ? i18n.t("score.acceptedShort") : i18n.t("score.pendingShort"),
        llm: score.accepted.llm ? i18n.t("score.acceptedShort") : i18n.t("score.pendingShort"),
      });
    }
  } else {
    elements.scoreNote.textContent = i18n.t("score.breakdown", {
      black: territoryBlack ?? 0,
      white: territoryWhite ?? 0,
    });
  }
}

/** @description 바둑판을 서버 스냅샷과 선택·계가 표시로 그립니다. */
function renderBoard() {
  const snapshot = ui.snapshot;
  const size = snapshot.board_size || 19;
  const legalMoves = new Set(snapshot.legal_moves || []);
  const stones = snapshot.stones || {};
  const score = snapshot.score;
  const dead = new Set(score?.dead || []);
  const seki = new Set(score?.seki || []);
  const territoryBlack = new Set(score?.territory?.black || []);
  const territoryWhite = new Set(score?.territory?.white || []);
  const lastMove = snapshot.last_move?.move;
  const activePoint = document.activeElement?.classList.contains("square")
    ? document.activeElement.dataset.point
    : null;
  const ordered = [];
  for (let rank = size; rank >= 1; rank -= 1) {
    for (let fileIndex = 0; fileIndex < size; fileIndex += 1) {
      ordered.push(`${FILES[fileIndex]}${rank}`);
    }
  }
  elements.boardGridShell.style.setProperty("--board-size", size);
  elements.board.style.setProperty("--board-size", size);
  elements.board.dataset.locked = String(!(canHumanMove() || canScoreEdit()));
  elements.rankGutter.replaceChildren();
  for (let rank = size; rank >= 1; rank -= 1) {
    const label = document.createElement("span");
    label.className = "gutter-label";
    label.textContent = String(rank);
    elements.rankGutter.append(label);
  }
  elements.fileGutter.replaceChildren();
  for (let fileIndex = 0; fileIndex < size; fileIndex += 1) {
    const label = document.createElement("span");
    label.className = "gutter-label";
    label.textContent = FILES[fileIndex];
    elements.fileGutter.append(label);
  }
  elements.board.replaceChildren();
  ordered.forEach((point, index) => {
    const button = document.createElement("button");
    const stone = stones[point];
    const fileIndex = index % size;
    const rowIndex = Math.floor(index / size);
    const isLegal = legalMoves.has(point);
    button.type = "button";
    button.className = `square ${(rowIndex + fileIndex) % 2 === 0 ? "square-light" : "square-dark"}`;
    button.dataset.point = point;
    button.tabIndex = 0;
    button.setAttribute("aria-pressed", String(point === ui.selectedPoint || dead.has(point) || seki.has(point)));
    const canEditPoint = canScoreEdit() && Boolean(stone);
    button.setAttribute("aria-disabled", String(!(canHumanMove() || canEditPoint)));
    const description = stone
      ? i18n.t("point.stone", { point: pointName(point), color: colorName(stone) })
      : i18n.t("point.empty", { point: pointName(point) });
    button.setAttribute("aria-label", `${description}${isLegal ? `, ${i18n.t("point.legal")}` : ""}`);
    const pointMatch = point.match(/^([A-T]+)(\d+)$/);
    const pointFile = FILES.indexOf(pointMatch[1]) + 1;
    const pointRank = Number(pointMatch[2]);
    if (STAR_POINTS[size].includes(pointFile) && STAR_POINTS[size].includes(pointRank)) {
      button.classList.add("is-star");
    }
    if (point === ui.selectedPoint) {
      button.classList.add("is-selected");
    }
    if (lastMove === point) {
      button.classList.add("is-last-move");
    }
    if (dead.has(point)) {
      button.classList.add("is-marked-dead");
    }
    if (seki.has(point)) {
      button.classList.add("is-marked-seki");
    }
    if (territoryBlack.has(point)) {
      button.classList.add("is-territory-black");
    } else if (territoryWhite.has(point)) {
      button.classList.add("is-territory-white");
    }
    if (isLegal) {
      button.classList.add("is-legal");
    }
    const gridLine = document.createElement("span");
    gridLine.className = "grid-line";
    gridLine.setAttribute("aria-hidden", "true");
    button.append(gridLine);
    if (button.classList.contains("is-star")) {
      const star = document.createElement("span");
      star.className = "star-point";
      star.setAttribute("aria-hidden", "true");
      button.append(star);
    }
    if (stone) {
      const stoneElement = document.createElement("span");
      stoneElement.className = `stone stone-${stone}`;
      stoneElement.setAttribute("aria-hidden", "true");
      button.append(stoneElement);
    }
    button.addEventListener("click", () => handlePointClick(point));
    elements.board.append(button);
  });
  if (activePoint) {
    elements.board.querySelector(`[data-point="${activePoint}"]`)?.focus();
  }
}

/** @description 착점 또는 계가 표시 모드에 따라 한 교차점을 처리합니다. */
function handlePointClick(point) {
  if (canScoreEdit()) {
    if (!ui.snapshot.stones[point]) return;
    submitScore(ui.scoreMode, point);
    return;
  }
  if (!canHumanMove()) {
    return;
  }
  if (!ui.selectedPoint) {
    if (new Set(ui.snapshot.legal_moves).has(point)) {
      submitHumanMove(point);
    }
    return;
  }
  if (ui.selectedPoint === point) {
    ui.selectedPoint = null;
    renderBoard();
  }
}

/** @description 화살표로 고정 방향 바둑판의 다음 교차점에 포커스를 이동합니다. */
function moveBoardFocus(point, key) {
  const size = ui.snapshot.board_size || 19;
  const fileIndex = FILES.indexOf(point.slice(0, -1));
  const rank = Number(point.slice(1));
  let nextFile = fileIndex;
  let nextRank = rank;
  if (key === "ArrowLeft") nextFile -= 1;
  if (key === "ArrowRight") nextFile += 1;
  if (key === "ArrowUp") nextRank += 1;
  if (key === "ArrowDown") nextRank -= 1;
  if (nextFile < 0 || nextFile >= size || nextRank < 1 || nextRank > size) {
    return;
  }
  elements.board.querySelector(`[data-point="${FILES[nextFile]}${nextRank}"]`)?.focus();
}

/** @description 포커스된 교차점에서 화살표·Enter·Space 키를 처리합니다. */
function handleBoardKeydown(event) {
  const focused = document.activeElement?.classList.contains("square")
    ? document.activeElement.dataset.point
    : null;
  if (focused && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) {
    event.preventDefault();
    moveBoardFocus(focused, event.key);
  } else if (focused && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    handlePointClick(focused);
  }
}

/** @description 마지막 수와 행위자를 오른쪽 레일에 표시합니다. */
function renderLastMove() {
  const move = ui.snapshot.last_move;
  if (!move) {
    elements.lastMoveValue.textContent = i18n.t("lastMove.empty");
    elements.lastMoveMeta.textContent = i18n.t("lastMove.waiting");
    return;
  }
  elements.lastMoveValue.textContent = moveName(move.move);
  elements.lastMoveMeta.textContent = i18n.t("lastMove.meta", {
    actor: actorName(move.actor),
    color: colorName(move.color),
    captured: move.captured.length,
  });
}

/** @description 바둑 수순을 한 수씩 스크롤 가능한 목록으로 표시합니다. */
function renderMoveHistory() {
  const history = ui.snapshot.move_history;
  elements.moveList.replaceChildren();
  elements.moveCount.textContent = i18n.t("history.count", { count: history.length });
  elements.moveCount.setAttribute("aria-label", i18n.t("history.count", { count: history.length }));
  elements.emptyHistory.hidden = history.length > 0;
  history.forEach((move) => {
    const item = document.createElement("li");
    item.className = move.actor === "human" ? "is-human" : move.actor === "llm" ? "is-llm" : `is-${move.color}`;
    item.setAttribute("aria-label", i18n.t("history.itemAria", {
      ply: move.ply,
      move: moveName(move.move),
      actor: actorName(move.actor),
      color: colorName(move.color),
    }));
    const ply = document.createElement("span");
    const moveText = document.createElement("span");
    const actor = document.createElement("span");
    const captured = document.createElement("span");
    ply.className = "move-number";
    moveText.className = "move-san";
    actor.className = "move-actor";
    captured.className = "move-capture";
    ply.textContent = `${move.ply}.`;
    moveText.textContent = moveName(move.move);
    actor.textContent = actorName(move.actor);
    captured.textContent = move.captured.length ? `+${move.captured.length}` : "";
    item.append(ply, moveText, actor, captured);
    elements.moveList.append(item);
  });
  elements.moveList.scrollTop = elements.moveList.scrollHeight;
}

/** @description 전체 화면을 스냅샷 기준으로 한 번 그립니다. */
function render() {
  const snapshot = ui.snapshot;
  const setupWasHidden = elements.setupLayer.hidden;
  elements.appShell.dataset.status = snapshot.status;
  elements.matchId.textContent = snapshot.game_id
    ? i18n.t("match.game", { id: snapshot.game_id.slice(0, 8) })
    : i18n.t("match.none");
  if (!snapshot.game_id) {
    elements.boardCaption.textContent = i18n.t("board.chooseColor");
  } else if (isCliMode()) {
    elements.boardCaption.textContent = i18n.t("board.caption.cli", {
      black: playerName("black"),
      white: playerName("white"),
      size: snapshot.board_size,
    });
  } else {
    elements.boardCaption.textContent = i18n.t(snapshot.status === "scoring" ? "board.caption.scoring" : snapshot.turn === "human" ? "board.caption.human" : snapshot.turn === "llm" ? "board.caption.llm" : "board.caption.terminal", {
      color: colorName(snapshot.human_color),
      size: snapshot.board_size,
    });
  }
  elements.boardStatus.textContent = statusText();
  elements.revisionLabel.textContent = i18n.t("board.revision", { revision: snapshot.revision });
  renderClock();
  renderParticipants();
  renderConnection();
  renderBoard();
  renderLastMove();
  renderMoveHistory();
  renderScore();
  const scoring = snapshot.status === "scoring";
  elements.scoreModeControls.hidden = !scoring || isCliMode();
  elements.passButton.hidden = isCliMode() || scoring || snapshot.status !== "active";
  elements.newGameButton.disabled = ui.requestPending;
  elements.takebackButton.hidden = isCliMode();
  elements.resignButton.hidden = isCliMode();
  elements.takebackButton.disabled = isCliMode() || !canRequestTakeback();
  elements.resignButton.disabled = isCliMode() || !canResign();
  elements.passButton.disabled = !canHumanMove() || !new Set(snapshot.legal_moves).has("pass");
  elements.setupStartButton.disabled = ui.requestPending;
  elements.colorButtons.forEach((button) => {
    button.disabled = ui.requestPending;
    button.classList.toggle("is-selected", button.dataset.color === ui.setupColor);
    button.setAttribute("aria-pressed", String(button.dataset.color === ui.setupColor));
  });
  elements.sizeButtons.forEach((button) => {
    button.disabled = ui.requestPending;
    button.classList.toggle("is-selected", Number(button.dataset.size) === ui.setupSize);
    button.setAttribute("aria-pressed", String(Number(button.dataset.size) === ui.setupSize));
  });
  elements.modeButtons.forEach((button) => {
    button.disabled = ui.requestPending;
    button.classList.toggle("is-selected", button.dataset.mode === ui.setupMode);
    button.setAttribute("aria-pressed", String(button.dataset.mode === ui.setupMode));
  });
  elements.humanColorFields.hidden = isSetupCliMode();
  elements.cliNameFields.hidden = !isSetupCliMode();
  elements.deadModeButton.dataset.active = String(ui.scoreMode === "dead");
  elements.sekiModeButton.dataset.active = String(ui.scoreMode === "seki");
  elements.deadModeButton.setAttribute("aria-pressed", String(ui.scoreMode === "dead"));
  elements.sekiModeButton.setAttribute("aria-pressed", String(ui.scoreMode === "seki"));
  elements.scoreAcceptButton.disabled = !canAcceptScore();
  elements.scoreResumeButton.disabled = isCliMode() || !scoring || ui.requestPending;
  elements.setupLayer.hidden = !ui.setupOpen;
  renderGuide();
  elements.topbar.inert = ui.setupOpen;
  elements.workspace.inert = ui.setupOpen;
  elements.setupError.hidden = !ui.error || !ui.setupOpen;
  elements.setupError.textContent = errorText();
  renderActionDialog();
  if (ui.setupOpen && setupWasHidden) {
    requestAnimationFrame(() => elements.colorButtons[0].focus());
  } else if (!ui.setupOpen && !setupWasHidden) {
    const returnFocus = ui.setupReturnFocus || elements.newGameButton;
    ui.setupReturnFocus = null;
    requestAnimationFrame(() => returnFocus.focus());
  }
}

/** @description 무르기·기권 대화상자의 현재 모드와 현지화 문구를 그립니다. */
function renderActionDialog() {
  if (isCliMode()) {
    ui.actionDialogMode = null;
    if (elements.actionDialog.open) elements.actionDialog.close();
    return;
  }
  const pending = ui.snapshot.takeback;
  const incoming = isTakebackPending() && pending.requester === "llm";
  if (incoming && ui.actionDialogMode !== "takeback-response") {
    ui.actionDialogMode = "takeback-response";
  }
  if (ui.actionDialogMode === "takeback-response" && !incoming) {
    ui.actionDialogMode = null;
  }
  if (ui.actionDialogMode === "takeback-request" && !canRequestTakeback()) {
    ui.actionDialogMode = null;
  }
  if (ui.actionDialogMode === "resign-confirm" && !canResign()) {
    ui.actionDialogMode = null;
  }
  if (!ui.actionDialogMode) {
    if (elements.actionDialog.open) elements.actionDialog.close();
    return;
  }
  const preview = ui.actionDialogMode === "takeback-response" ? pending : takebackPreview();
  const isResponse = ui.actionDialogMode === "takeback-response";
  const isResign = ui.actionDialogMode === "resign-confirm";
  const copy = isResign ? {
    eyebrow: i18n.t("resign.dialog.eyebrow"),
    heading: i18n.t("resign.heading"),
    description: i18n.t("resign.description"),
    aria: i18n.t("resign.aria"),
  } : isResponse ? {
    eyebrow: i18n.t("takeback.dialog.eyebrow"),
    heading: i18n.t("takeback.response.heading"),
    description: i18n.t("takeback.response.description", { plies: preview.undone_plies, target: preview.target_ply }),
    aria: i18n.t("takeback.aria"),
  } : {
    eyebrow: i18n.t("takeback.dialog.eyebrow"),
    heading: i18n.t("takeback.request.heading"),
    description: i18n.t("takeback.request.description", { plies: preview.undone_plies, target: preview.target_ply }),
    aria: i18n.t("takeback.aria"),
  };
  elements.actionDialogEyebrow.textContent = copy.eyebrow;
  elements.actionDialogHeading.textContent = copy.heading;
  elements.actionDialogDescription.textContent = copy.description;
  elements.actionDialog.setAttribute("aria-label", copy.aria);
  elements.actionDialogError.hidden = !ui.error;
  elements.actionDialogError.textContent = errorText();
  elements.actionDialogCancel.hidden = isResponse;
  elements.actionDialogReject.hidden = !isResponse;
  elements.actionDialogAccept.hidden = !isResponse;
  elements.actionDialogPrimary.hidden = isResponse || isResign;
  elements.actionDialogResign.hidden = !isResign;
  if (!elements.actionDialog.open) elements.actionDialog.showModal();
}

/* =================================== 서버 행동 =================================== */

/** @description 사람의 착점 또는 패스를 서버에 제출합니다. */
async function submitHumanMove(move) {
  if (!canHumanMove()) return;
  ui.requestPending = true;
  ui.selectedPoint = null;
  ui.error = null;
  render();
  try {
    const snapshot = await requestJson("/api/human/moves", {
      method: "POST",
      body: JSON.stringify({ move }),
    });
    applySnapshot(snapshot);
    ui.connection = "connected";
  } catch (error) {
    ui.error = localizedErrorState(error, "error.move");
  } finally {
    ui.requestPending = false;
    render();
  }
}

/** @description 사람의 무르기 요청·승인·거부를 서버에 제출합니다. */
async function submitTakeback(action) {
  if (ui.requestPending) return;
  if (action === "request" && !canRequestTakeback()) return;
  if ((action === "accept" || action === "reject") && !isTakebackPending()) return;
  ui.requestPending = true;
  ui.error = null;
  render();
  try {
    const snapshot = await requestJson("/api/human/takeback", {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    applySnapshot(snapshot);
    ui.connection = "connected";
    ui.actionDialogMode = null;
  } catch (error) {
    ui.error = localizedErrorState(error, "error.takeback");
  } finally {
    ui.requestPending = false;
    render();
  }
}

/** @description 사람의 기권을 서버에 제출합니다. */
async function submitResignation() {
  if (!canResign()) return;
  ui.requestPending = true;
  ui.error = null;
  render();
  try {
    const snapshot = await requestJson("/api/human/resign", { method: "POST" });
    applySnapshot(snapshot);
    ui.connection = "connected";
    ui.actionDialogMode = null;
  } catch (error) {
    ui.error = localizedErrorState(error, "error.resign");
  } finally {
    ui.requestPending = false;
    render();
  }
}

/** @description 현재 표시된 revision을 계가 수락 요청에 함께 제출합니다. */
async function submitScore(action, point = null) {
  if (ui.requestPending) return;
  if ((action === "dead" || action === "seki") && !canScoreEdit()) return;
  if (action === "accept" && !canAcceptScore()) return;
  if (action === "resume" && ui.snapshot.status !== "scoring") return;
  ui.requestPending = true;
  ui.error = null;
  render();
  const body = { action };
  if (point) body.point = point;
  if (action === "accept") body.revision = ui.snapshot.revision;
  try {
    const snapshot = await requestJson("/api/human/score", {
      method: "POST",
      body: JSON.stringify(body),
    });
    applySnapshot(snapshot);
    ui.connection = "connected";
  } catch (error) {
    ui.error = localizedErrorState(error, "error.score");
  } finally {
    ui.requestPending = false;
    render();
  }
}

/* =================================== 게임 시작과 이벤트 =================================== */

/** @description 새 게임 설정 표면을 엽니다. */
function openNewGame() {
  if (ui.snapshot.move_history.length > 0) {
    if (!window.confirm(i18n.t("confirm.newGame"))) return;
  }
  ui.setupReturnFocus = elements.newGameButton;
  ui.setupMode = ui.snapshot.game_mode || "human_vs_llm";
  ui.setupColor = ui.snapshot.human_color || "black";
  ui.setupSize = ui.snapshot.board_size || 19;
  elements.blackName.value = playerForColor("black").name || "";
  elements.whiteName.value = playerForColor("white").name || "";
  ui.setupOpen = true;
  ui.error = null;
  ui.scoreMode = null;
  render();
}

/** @description 선택한 모드와 판 크기로 새 메모리 게임을 시작합니다. */
async function startGame() {
  ui.requestPending = true;
  ui.error = null;
  render();
  const body = {
    game_mode: ui.setupMode,
    board_size: ui.setupSize,
  };
  if (ui.setupMode === "human_vs_llm") {
    body.human_color = ui.setupColor;
  } else {
    body.black_name = elements.blackName.value.trim() || null;
    body.white_name = elements.whiteName.value.trim() || null;
  }
  try {
    const snapshot = await requestJson("/api/games", {
      method: "POST",
      body: JSON.stringify(body),
    });
    applySnapshot(snapshot);
    ui.setupOpen = false;
    ui.connection = "connected";
  } catch (error) {
    ui.connection = "error";
    ui.error = localizedErrorState(error, "error.start");
  } finally {
    ui.requestPending = false;
    render();
  }
}

/** @description 선택한 CLI 명령 또는 세션 프롬프트를 클립보드에 복사합니다. */
async function copyGuideText(button) {
  const color = button.dataset.copyColor;
  const textElement = button.dataset.copyKind === "command"
    ? [...elements.guideCommands].find((element) => element.dataset.guideCommand === color)
    : [...elements.guidePrompts].find((element) => element.dataset.guidePrompt === color);
  try {
    await navigator.clipboard.writeText(textElement.textContent);
    button.textContent = i18n.t("guide.copied");
    window.setTimeout(() => { button.textContent = i18n.t(button.dataset.i18n); }, 1500);
  } catch {
    ui.error = { key: "guide.copyError", values: {} };
    render();
  }
}

/** @description 서버 이벤트 스트림을 열고 브라우저 기본 재연결을 사용합니다. */
function connectEvents() {
  const stream = new EventSource("/api/events");
  stream.addEventListener("open", () => {
    ui.connection = "connected";
    ui.error = null;
    render();
  });
  stream.addEventListener("message", handleServerEvent);
  stream.addEventListener("error", () => {
    ui.connection = "disconnected";
    render();
  });
}

/** @description 브라우저 입력과 버튼 이벤트를 연결합니다. */
function bindEvents() {
  elements.board.addEventListener("keydown", handleBoardKeydown);
  elements.newGameButton.addEventListener("click", openNewGame);
  elements.takebackButton.addEventListener("click", () => {
    ui.actionDialogMode = "takeback-request";
    ui.error = null;
    render();
  });
  elements.resignButton.addEventListener("click", () => {
    ui.actionDialogMode = "resign-confirm";
    ui.error = null;
    render();
  });
  elements.passButton.addEventListener("click", () => submitHumanMove("pass"));
  elements.setupStartButton.addEventListener("click", startGame);
  elements.modeButtons.forEach((button) => button.addEventListener("click", () => {
    ui.setupMode = button.dataset.mode;
    render();
  }));
  elements.colorButtons.forEach((button) => button.addEventListener("click", () => {
    ui.setupColor = button.dataset.color;
    render();
  }));
  elements.sizeButtons.forEach((button) => button.addEventListener("click", () => {
    ui.setupSize = Number(button.dataset.size);
    render();
  }));
  elements.deadModeButton.addEventListener("click", () => {
    ui.scoreMode = "dead";
    render();
  });
  elements.sekiModeButton.addEventListener("click", () => {
    ui.scoreMode = "seki";
    render();
  });
  elements.scoreAcceptButton.addEventListener("click", () => submitScore("accept"));
  elements.scoreResumeButton.addEventListener("click", () => submitScore("resume"));
  elements.localeSelects.forEach((select) => select.addEventListener("change", () => i18n.setLocale(select.value)));
  elements.guideCopyButtons.forEach((button) => button.addEventListener("click", () => copyGuideText(button)));
  elements.actionDialogCancel.addEventListener("click", closeActionDialog);
  elements.actionDialogPrimary.addEventListener("click", () => submitTakeback("request"));
  elements.actionDialogReject.addEventListener("click", () => submitTakeback("reject"));
  elements.actionDialogAccept.addEventListener("click", () => submitTakeback("accept"));
  elements.actionDialogResign.addEventListener("click", submitResignation);
  elements.actionDialog.addEventListener("cancel", (event) => {
    if (ui.actionDialogMode === "takeback-response" && isTakebackPending()) {
      event.preventDefault();
      return;
    }
    ui.actionDialogMode = null;
  });
  elements.actionDialog.addEventListener("close", () => {
    if (ui.actionDialogMode === "takeback-response" && isTakebackPending()) {
      renderActionDialog();
      return;
    }
    ui.actionDialogMode = null;
  });
}

/** @description 닫을 수 있는 게임 동작 대화상자를 닫습니다. */
function closeActionDialog() {
  if (ui.actionDialogMode === "takeback-response" && isTakebackPending()) return;
  ui.actionDialogMode = null;
  ui.error = null;
  if (elements.actionDialog.open) elements.actionDialog.close();
  render();
}

i18n.subscribe(() => {
  applyStaticCopy();
  render();
});

applyStaticCopy();
bindEvents();
render();
loadState();
connectEvents();
