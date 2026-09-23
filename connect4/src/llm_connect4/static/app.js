/**
 * @file LLM Connect Four 브라우저 작업대
 * @description 서버 상태를 보드와 대국 조작에 반영합니다.
 */

const i18n = window.LlmConnect4I18n;
const initialSnapshot = {
  event: "setup", game_id: null, revision: 0, status: "setup", status_reason: "no_game",
  game_mode: null, players: {}, human_color: null, llm_color: null, turn: null, to_play: null,
  board: Array.from({ length: 6 }, () => Array(7).fill(null)), legal_columns: [],
  move_history: [], last_move: null, winning_line: [], takeback: null, resigned_by: null, winner: null, result: null,
};

const ui = {
  snapshot: initialSnapshot,
  setupOpen: true,
  setupMode: "human_vs_llm",
  setupColor: "red",
  setupReturnFocus: null,
  actionDialogMode: null,
  actionReturnFocus: null,
  connection: "connecting",
  error: null,
  restoreColumnFocus: false,
};

const elements = {
  appShell: document.querySelector("#app-shell"),
  matchId: document.querySelector("#match-id"),
  boardCaption: document.querySelector("#board-caption"),
  board: document.querySelector("#connect4-board"),
  dropColumns: document.querySelector("#drop-columns"),
  boardStatus: document.querySelector("#board-status"),
  statusDot: document.querySelector("#status-dot"),
  revisionLabel: document.querySelector("#revision-label"),
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
  setupPanel: document.querySelector(".setup-panel"),
  setupError: document.querySelector("#setup-error"),
  setupStartButton: document.querySelector("#setup-start-button"),
  modeButtons: document.querySelectorAll(".mode-choice [data-mode]"),
  humanColorFields: document.querySelector("#human-color-fields"),
  redName: document.querySelector("#red-name"),
  yellowName: document.querySelector("#yellow-name"),
  newGameButton: document.querySelector("#new-game-button"),
  takebackButton: document.querySelector("#takeback-button"),
  resignButton: document.querySelector("#resign-button"),
  guideSection: document.querySelector("#guide-section"),
  guideCommands: document.querySelectorAll("[data-guide-command]"),
  guidePrompts: document.querySelectorAll("[data-guide-prompt]"),
  guideTitles: document.querySelectorAll("[data-guide-title]"),
  guideCopyButtons: document.querySelectorAll("[data-copy-kind]"),
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
  localeSelects: document.querySelectorAll("[data-locale-select]"),
};

const errorKeys = {
  no_game: "error.noGame", game_over: "error.gameOver", wrong_turn: "error.wrongTurn",
  illegal_move: "error.illegalMove", invalid_color: "error.invalidColor", invalid_game_mode: "error.invalidGameMode",
  takeback_unavailable: "error.takebackUnavailable", takeback_pending: "error.takebackPending",
  takeback_no_pending: "error.noPendingTakeback", takeback_own_request: "error.takebackOwnRequest",
  takeback_no_move: "error.takebackNoMove", takeback_move_blocked: "error.takebackMoveBlocked",
  player_not_cli: "error.playerNotCli", color_required: "error.colorRequired",
};

/** @description 화면의 정적 문구를 현재 언어로 바꿉니다. */
function applyStaticCopy() {
  document.title = i18n.t("meta.title");
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = i18n.t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", i18n.t(element.dataset.i18nAriaLabel));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", i18n.t(element.dataset.i18nPlaceholder));
  });
  elements.localeSelects.forEach((select) => { select.value = i18n.getLocale(); });
  renderGuide();
}

/** @description CLI 대 CLI 도움말과 복사용 문구를 갱신합니다. */
function renderGuide() {
  const visible = isCliMode() || (ui.setupOpen && ui.setupMode === "cli_vs_cli");
  elements.guideSection.hidden = !visible;
  for (const color of ["red", "yellow"]) {
    const commands = [
      `connect4 --color ${color} wait`,
      `connect4 --color ${color} move 4`,
      `connect4 --color ${color} takeback request`,
      `connect4 --color ${color} takeback accept`,
      `connect4 --color ${color} takeback reject`,
      `connect4 --color ${color} resign`,
      "connect4 status",
    ].join("\n");
    const player = ui.snapshot.players[color];
    const title = player?.name || i18n.t("player.default", { color: i18n.t(`color.${color}`) });
    elements.guideCommands.forEach((element) => { if (element.dataset.guideCommand === color) element.textContent = commands; });
    elements.guidePrompts.forEach((element) => {
      if (element.dataset.guidePrompt === color) element.textContent = i18n.t("guide.prompt", { color });
    });
    elements.guideTitles.forEach((element) => { if (element.dataset.guideTitle === color) element.textContent = title; });
  }
}

/** @description 현재 연결·요청 오류를 표시합니다. */
function renderError() {
  elements.errorCopy.hidden = !ui.error;
  elements.errorCopy.textContent = ui.error ? i18n.t(ui.error.key, ui.error.values) : "";
}

/** @description 페이지 연결 상태를 표시합니다. */
function renderConnection() {
  const key = {
    connecting: "connection.connecting", connected: "connection.live",
    reconnecting: "connection.reconnecting", disconnected: "connection.disconnected",
  }[ui.connection];
  elements.connectionValue.textContent = i18n.t(key);
  elements.statusDot.dataset.state = ui.connection === "connected" ? "connected" : ui.connection === "disconnected" ? "disconnected" : "";
  elements.liveIndicator.dataset.state = ui.connection === "connected" ? "" : ui.connection === "disconnected" ? "error" : "waiting";
  elements.liveIndicator.querySelector("span").textContent = i18n.t(ui.connection === "connected" ? "connection.live" : ui.connection === "disconnected" ? "connection.error" : "connection.reconnecting");
  if (ui.connection === "disconnected") elements.boardStatus.textContent = i18n.t("status.connecting");
}

/** @description 행위자 이름에 쓸 현지화된 색 이름을 반환합니다. */
function colorName(color) {
  return i18n.t(`color.${color}`);
}

/** @description 현재 모드가 CLI 관전인지 반환합니다. */
function isCliMode() {
  return ui.snapshot.game_mode === "cli_vs_cli";
}

/** @description 서버가 현재 사람의 수를 받을 수 있는지 반환합니다. */
function canHumanMove() {
  return ui.snapshot.status === "active" && ui.snapshot.game_mode === "human_vs_llm"
    && ui.snapshot.turn === "human" && ui.snapshot.takeback?.state !== "pending";
}

/** @description 보드와 열 선택 단추를 서버 상태로 다시 그립니다. */
function renderBoard() {
  const focused = document.activeElement?.closest?.(".drop-button");
  const focusedColumn = focused ? Number(focused.dataset.column) : null;
  const legal = new Set(ui.snapshot.legal_columns);
  const enabled = canHumanMove();
  elements.board.setAttribute("aria-disabled", String(!enabled));
  elements.board.innerHTML = "";
  elements.dropColumns.querySelectorAll(".drop-button").forEach((button) => {
    const column = Number(button.dataset.column);
    button.disabled = !enabled || !legal.has(column);
    button.setAttribute("aria-label", i18n.t("board.column.label", { color: colorName(ui.snapshot.to_play || ui.setupColor), column }));
    button.tabIndex = column === 1 || (ui.restoreColumnFocus && column === focusedColumn) ? 0 : -1;
  });

  const lastMove = ui.snapshot.last_move;
  const winning = new Set(ui.snapshot.winning_line.map(([row, column]) => `${row}:${column}`));
  for (let row = 0; row < 6; row += 1) {
    const rowElement = document.createElement("div");
    rowElement.className = "board-row";
    rowElement.setAttribute("role", "row");
    rowElement.setAttribute("aria-rowindex", String(row + 1));
    for (let column = 0; column < 7; column += 1) {
      const color = ui.snapshot.board[row][column];
      const cell = document.createElement("div");
      cell.className = "board-cell";
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-colindex", String(column + 1));
      cell.setAttribute("aria-label", color
        ? i18n.t("board.cell.disc", { row: row + 1, column: column + 1, color: colorName(color) })
        : i18n.t("board.cell.empty", { row: row + 1, column: column + 1 }));
      const well = document.createElement("span");
      well.className = `cell-well${color ? ` disc-${color}` : ""}`;
      if (lastMove?.row === row && lastMove?.column === column + 1) well.classList.add("is-last");
      if (winning.has(`${row}:${column}`)) well.classList.add("is-winning");
      cell.append(well);
      rowElement.append(cell);
    }
    elements.board.append(rowElement);
  }

  if (focusedColumn !== null && ui.restoreColumnFocus) {
    const target = elements.dropColumns.querySelector(`[data-column="${focusedColumn}"]`);
    if (target && !target.disabled) target.focus();
    else elements.boardStatus.focus();
    ui.restoreColumnFocus = false;
  }
}

/** @description 대국의 이름과 현재 차례를 레일에 표시합니다. */
function renderTurn() {
  const snapshot = ui.snapshot;
  const pending = snapshot.takeback?.state === "pending";
  const colors = ["red", "yellow"];
  let tone = "setup";
  let label = "clock.setup.label";
  let value = "clock.setup.value";
  let detail = "clock.setup.detail";
  if (snapshot.status === "active") {
    if (isCliMode()) {
      tone = "human";
      label = "clock.cli.label";
      value = "clock.cli.value";
      detail = pending ? "status.takeback" : "clock.cli.detail";
    } else if (snapshot.turn === "human") {
      tone = "human";
      label = "clock.human.label";
      value = "clock.human.value";
      detail = pending ? "status.takeback" : "clock.human.detail";
    } else {
      tone = "llm";
      label = "clock.llm.label";
      value = "clock.llm.value";
      detail = pending ? "status.takeback" : "clock.llm.detail";
    }
  } else if (snapshot.status === "won") {
    tone = "terminal"; label = "clock.won.label"; value = "clock.won.value"; detail = "clock.won.detail";
  } else if (snapshot.status === "draw") {
    tone = "terminal"; label = "clock.draw.label"; value = "clock.draw.value"; detail = "clock.draw.detail";
  } else if (snapshot.status === "resigned") {
    tone = "terminal"; label = "clock.resigned.label"; value = "clock.resigned.value"; detail = "clock.resigned.detail";
  }
  const color = snapshot.winner || snapshot.to_play || "red";
  elements.clockFace.dataset.tone = tone;
  elements.clockLabel.textContent = i18n.t(label);
  elements.clockValue.textContent = i18n.t(value, { color: colorName(color) });
  elements.clockDetail.textContent = i18n.t(detail, { color: colorName(color) });
  elements.participantStrip.replaceChildren();
  for (const currentColor of colors) {
    const player = snapshot.players[currentColor];
    const participant = document.createElement("div");
    participant.className = "participant";
    participant.dataset.active = String(snapshot.to_play === currentColor && snapshot.status === "active");
    const disc = document.createElement("span");
    disc.className = `color-disc disc-${currentColor}`;
    disc.setAttribute("aria-hidden", "true");
    const copy = document.createElement("span");
    copy.className = "participant-copy";
    const name = document.createElement("strong");
    name.className = "participant-name";
    const defaultName = i18n.t("player.default", { color: colorName(currentColor) });
    name.textContent = player?.name || (player?.actor === "human"
      ? i18n.t("player.human", { color: colorName(currentColor) })
      : player?.actor === "llm" ? i18n.t("player.llm", { color: colorName(currentColor) }) : defaultName);
    const colorLabel = document.createElement("span");
    colorLabel.className = "participant-color";
    colorLabel.textContent = colorName(currentColor);
    copy.append(name, colorLabel);
    participant.append(disc, copy);
    elements.participantStrip.append(participant);
  }
}

/** @description 현재 대국 상태에 맞는 보드 안내를 표시합니다. */
function renderStatus() {
  const snapshot = ui.snapshot;
  let key = "status.setup";
  const color = colorName(snapshot.winner || snapshot.to_play || "red");
  if (ui.connection === "connecting" && snapshot.status === "setup") key = "status.connecting";
  else if (snapshot.status === "active") {
    if (snapshot.takeback?.state === "pending") key = "status.takeback";
    else if (isCliMode()) key = "status.cli";
    else if (snapshot.turn === "human") key = "status.human";
    else key = "status.llm";
  } else if (snapshot.status === "won") key = "status.won";
  else if (snapshot.status === "draw") key = "status.draw";
  else if (snapshot.status === "resigned") key = "status.resigned";
  elements.boardStatus.textContent = i18n.t(key, { color });
  elements.revisionLabel.textContent = i18n.t("board.revision", { revision: snapshot.revision });
  elements.matchId.textContent = snapshot.game_id
    ? i18n.t("match.game", { id: snapshot.game_id.slice(0, 8) }) : i18n.t("match.none");
  let caption = "board.caption.setup";
  if (snapshot.status === "active") caption = isCliMode() ? "board.caption.cli" : snapshot.turn === "human" ? "board.caption.human" : "board.caption.llm";
  else if (["won", "draw", "resigned"].includes(snapshot.status)) caption = "board.caption.terminal";
  elements.boardCaption.textContent = i18n.t(caption, { color });
}

/** @description 마지막 수와 전체 수순을 갱신합니다. */
function renderHistory() {
  const moves = ui.snapshot.move_history;
  const last = ui.snapshot.last_move;
  elements.lastMoveValue.textContent = last ? i18n.t("lastMove.value", { column: last.column }) : i18n.t("lastMove.empty");
  elements.lastMoveMeta.textContent = last
    ? i18n.t("lastMove.meta", { color: colorName(last.color), ply: last.ply }) : i18n.t("lastMove.waiting");
  elements.moveCount.textContent = String(moves.length);
  elements.moveCount.setAttribute("aria-label", i18n.t("history.count", { count: moves.length }));
  elements.moveList.replaceChildren();
  for (const move of moves) {
    const item = document.createElement("li");
    item.setAttribute("aria-label", i18n.t("history.entry", { ply: move.ply, color: colorName(move.color), column: move.column }));
    const number = document.createElement("span");
    number.className = "move-number";
    number.textContent = String(move.ply);
    const disc = document.createElement("span");
    disc.className = `color-disc disc-${move.color}`;
    disc.setAttribute("aria-hidden", "true");
    const text = document.createElement("span");
    text.textContent = i18n.t("history.entry", { ply: move.ply, color: colorName(move.color), column: move.column });
    item.append(number, disc, text);
    elements.moveList.append(item);
  }
  elements.emptyHistory.hidden = moves.length > 0;
  elements.moveList.hidden = moves.length === 0;
}

/** @description 설정 대화상자 입력과 게임 동작을 동기화합니다. */
function renderControls() {
  const snapshot = ui.snapshot;
  const spectator = isCliMode();
  const hasHumanMove = snapshot.move_history.some((move) => move.actor === "human");
  const activeOrJustFinished = ["active", "won", "draw"].includes(snapshot.status);
  elements.takebackButton.hidden = spectator;
  elements.resignButton.hidden = spectator;
  elements.takebackButton.disabled = !hasHumanMove || !activeOrJustFinished || snapshot.takeback?.state === "pending";
  elements.resignButton.disabled = snapshot.status !== "active";
  elements.setupLayer.hidden = !ui.setupOpen;
  elements.setupPanel.dataset.mode = ui.setupMode;
  elements.humanColorFields.hidden = ui.setupMode !== "human_vs_llm";
  elements.modeButtons.forEach((button) => {
    const selected = button.dataset.mode === ui.setupMode;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  elements.colorButtons.forEach((button) => {
    const selected = button.dataset.color === ui.setupColor;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  renderGuide();
}

/** @description 전체 상태를 화면에 반영합니다. */
function render() {
  applyStaticCopy();
  renderBoard();
  renderTurn();
  renderStatus();
  renderHistory();
  renderControls();
  renderConnection();
  renderError();
  const takeback = ui.snapshot.takeback;
  if (!ui.setupOpen && !elements.actionDialog.open && isHumanMode() && takeback?.state === "pending" && takeback.requester === "llm") {
    openActionDialog("takeback-response");
  }
}

/** @description 현재 게임이 사람 대 LLM인지 반환합니다. */
function isHumanMode() {
  return ui.snapshot.game_mode === "human_vs_llm";
}

/** @description 서버 오류를 현재 언어의 문구로 저장합니다. */
function setApiError(error, fallbackKey) {
  if (error instanceof ApiError) {
    const move = error.code === "illegal_move" ? error.message.replace(/^Illegal move:\s*/, "") : error.message;
    ui.error = { key: errorKeys[error.code] || fallbackKey, values: { move } };
  }
  else ui.error = { key: fallbackKey, values: {} };
  renderError();
}

class ApiError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

/** @description JSON 요청을 보내고 서버의 도메인 오류를 보존합니다. */
async function request(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload.detail || {};
    throw new ApiError(detail.code, detail.message || "Request failed");
  }
  return payload;
}

/** @description 서버의 전체 스냅샷을 저장하고 화면을 갱신합니다. */
function applySnapshot(snapshot) {
  ui.snapshot = snapshot;
  if (snapshot.status === "setup") {
    ui.setupOpen = true;
  } else {
    ui.setupOpen = false;
    if (["game_started", "game_reset"].includes(snapshot.event)) {
      ui.setupMode = snapshot.game_mode;
      ui.setupColor = snapshot.human_color || "red";
      elements.redName.value = snapshot.players.red?.name || "";
      elements.yellowName.value = snapshot.players.yellow?.name || "";
    }
  }
  render();
}

/** @description 초기 상태를 읽고 서버 푸시 이벤트를 구독합니다. */
async function connect() {
  try {
    applySnapshot(await request("/api/state"));
    ui.connection = "connected";
  } catch {
    ui.connection = "disconnected";
    ui.error = { key: "error.connect", values: {} };
  }
  const source = new EventSource("/api/events");
  source.addEventListener("state", (event) => {
    applySnapshot(JSON.parse(event.data));
    if (ui.connection !== "connected") ui.connection = "connected";
    if (ui.error?.key === "error.connect") ui.error = null;
    renderConnection();
    renderError();
  });
  source.onopen = () => {
    ui.connection = "connected";
    if (ui.error?.key === "error.connect") ui.error = null;
    renderConnection();
    renderError();
  };
  source.onerror = () => {
    ui.connection = "reconnecting";
    renderConnection();
  };
  render();
}

/** @description 보드 열을 선택해 사람의 수를 전송합니다. */
async function dropColumn(column) {
  if (!canHumanMove() || !ui.snapshot.legal_columns.includes(column)) return;
  ui.restoreColumnFocus = true;
  try {
    applySnapshot(await request("/api/human/moves", { method: "POST", body: { move: String(column) } }));
    ui.error = null;
  } catch (error) {
    setApiError(error, "error.move");
  }
  render();
}

/** @description 새 대국을 만들고 설정 화면을 닫습니다. */
async function startGame() {
  elements.setupStartButton.disabled = true;
  elements.setupStartButton.textContent = i18n.t("setup.starting");
  elements.setupError.hidden = true;
  try {
    const snapshot = await request("/api/games", {
      method: "POST",
      body: {
        game_mode: ui.setupMode,
        human_color: ui.setupMode === "human_vs_llm" ? ui.setupColor : null,
        red_name: elements.redName.value,
        yellow_name: elements.yellowName.value,
      },
    });
    ui.error = null;
    applySnapshot(snapshot);
    elements.boardStatus.focus({ preventScroll: true });
  } catch (error) {
    const key = error instanceof ApiError ? errorKeys[error.code] || "error.start" : "error.start";
    elements.setupError.textContent = i18n.t(key, { move: error.message });
    elements.setupError.hidden = false;
  } finally {
    elements.setupStartButton.disabled = false;
    elements.setupStartButton.textContent = i18n.t("setup.start");
  }
  render();
}

/** @description 보호가 필요한 게임 동작의 대화상자를 표시합니다. */
function openActionDialog(mode) {
  ui.actionDialogMode = mode;
  ui.actionReturnFocus = document.activeElement;
  elements.actionDialogError.hidden = true;
  elements.actionDialogReject.hidden = mode !== "takeback-response";
  elements.actionDialogAccept.hidden = mode !== "takeback-response";
  elements.actionDialogPrimary.hidden = !["takeback-request", "new-game"].includes(mode);
  elements.actionDialogResign.hidden = mode !== "resign";
  elements.actionDialogCancel.hidden = mode === "takeback-response";
  const copy = {
    "takeback-request": ["takeback.request.heading", "takeback.request.description", "takeback.request.confirm"],
    "takeback-response": ["takeback.response.heading", "takeback.response.description", null],
    resign: ["resign.heading", "resign.description", null],
    "new-game": ["newGame.heading", "newGame.description", "newGame.confirm"],
  }[mode];
  elements.actionDialogHeading.textContent = i18n.t(copy[0]);
  elements.actionDialogDescription.textContent = i18n.t(copy[1]);
  if (copy[2]) elements.actionDialogPrimary.textContent = i18n.t(copy[2]);
  elements.actionDialogEyebrow.textContent = i18n.t("dialog.eyebrow");
  elements.actionDialog.setAttribute("aria-label", i18n.t(mode.startsWith("takeback") ? "takeback.aria" : "dialog.eyebrow"));
  elements.actionDialog.showModal();
  (mode === "takeback-response" ? elements.actionDialogAccept : mode === "resign" ? elements.actionDialogResign : elements.actionDialogPrimary).focus();
}

/** @description 동작 대화상자를 닫고 적절한 위치로 포커스를 돌립니다. */
function closeActionDialog() {
  if (elements.actionDialog.open) elements.actionDialog.close();
  ui.actionDialogMode = null;
  const target = ui.actionReturnFocus;
  ui.actionReturnFocus = null;
  if (target?.isConnected && !target.disabled && !target.hidden) target.focus({ preventScroll: true });
}

/** @description 확인된 동작을 서버에 전송합니다. */
async function submitAction(action) {
  const mode = ui.actionDialogMode;
  closeActionDialog();
  const routes = {
    "takeback-request": ["/api/human/takeback", { action: "request" }, "error.takeback"],
    "takeback-response": [`/api/human/takeback`, { action }, "error.takeback"],
    resign: ["/api/human/resign", undefined, "error.resign"],
  };
  if (mode === "new-game") {
    showSetup();
    return;
  }
  const [path, body, fallback] = routes[mode];
  try {
    applySnapshot(await request(path, { method: "POST", body }));
    ui.error = null;
  } catch (error) {
    setApiError(error, fallback);
  }
  render();
}

/** @description 새 대국 설정 화면을 열고 입력에 포커스를 둡니다. */
function showSetup() {
  ui.setupReturnFocus = document.activeElement;
  ui.setupOpen = true;
  ui.setupMode = ui.snapshot.game_mode || "human_vs_llm";
  ui.setupColor = ui.snapshot.human_color || "red";
  renderControls();
  const target = ui.setupMode === "human_vs_llm"
    ? document.querySelector(`[data-color="${ui.setupColor}"]`)
    : document.querySelector(`[data-mode="${ui.setupMode}"]`);
  target?.focus({ preventScroll: true });
}

/** @description 설정 화면을 닫고 열기 전 위치로 포커스를 복원합니다. */
function closeSetup() {
  ui.setupOpen = false;
  renderControls();
  if (ui.setupReturnFocus?.isConnected) ui.setupReturnFocus.focus({ preventScroll: true });
  else elements.newGameButton.focus({ preventScroll: true });
}

/** @description 색상과 대국 방식 선택 단추 상태를 갱신합니다. */
function selectSetupChoice(event) {
  const mode = event.target.closest("[data-mode]");
  const color = event.target.closest("[data-color]");
  if (mode) ui.setupMode = mode.dataset.mode;
  if (color) ui.setupColor = color.dataset.color;
  renderControls();
}

/** @description 복사 단추가 고른 CLI 안내를 클립보드에 복사합니다. */
async function copyGuide(event) {
  const button = event.target.closest("[data-copy-kind]");
  if (!button) return;
  const selector = button.dataset.copyKind === "command" ? "[data-guide-command]" : "[data-guide-prompt]";
  const content = [...document.querySelectorAll(selector)].find((item) => item.dataset[button.dataset.copyKind === "command" ? "guideCommand" : "guidePrompt"] === button.dataset.copyColor)?.textContent;
  await navigator.clipboard.writeText(content);
  const previous = button.textContent;
  button.textContent = i18n.t("guide.copySuccess");
  window.setTimeout(() => { button.textContent = previous; }, 1400);
}

/** @description 페이지 조작과 키보드 접근을 연결합니다. */
function bindEvents() {
  elements.board.addEventListener("click", (event) => {
    const cell = event.target.closest(".board-cell");
    if (cell) dropColumn(Number(cell.getAttribute("aria-colindex")));
  });
  elements.dropColumns.addEventListener("click", (event) => {
    const button = event.target.closest(".drop-button");
    if (button && !button.disabled) dropColumn(Number(button.dataset.column));
  });
  elements.dropColumns.addEventListener("focusin", (event) => {
    if (event.target.matches(".drop-button")) ui.restoreColumnFocus = true;
  });
  elements.dropColumns.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    const buttons = [...elements.dropColumns.querySelectorAll(".drop-button:not(:disabled)")];
    if (!buttons.length) return;
    const index = buttons.indexOf(document.activeElement);
    const step = event.key === "ArrowRight" ? 1 : -1;
    buttons[(index + step + buttons.length) % buttons.length].focus();
    event.preventDefault();
  });
  window.addEventListener("keydown", (event) => {
    if (/^[1-7]$/.test(event.key) && !event.altKey && !event.ctrlKey && !event.metaKey
      && !["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)
      && !ui.setupOpen && !elements.actionDialog.open) dropColumn(Number(event.key));
    if (event.key === "Tab" && ui.setupOpen) {
      const focusable = [...elements.setupPanel.querySelectorAll("button:not(:disabled), input:not(:disabled), select:not(:disabled)")];
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { last.focus(); event.preventDefault(); }
      else if (!event.shiftKey && document.activeElement === last) { first.focus(); event.preventDefault(); }
    }
    if (event.key === "Escape" && ui.setupOpen && ui.snapshot.status !== "setup") closeSetup();
  });
  elements.newGameButton.addEventListener("click", () => {
    if (ui.snapshot.status === "setup") showSetup();
    else openActionDialog("new-game");
  });
  elements.takebackButton.addEventListener("click", () => openActionDialog("takeback-request"));
  elements.resignButton.addEventListener("click", () => openActionDialog("resign"));
  elements.setupStartButton.addEventListener("click", startGame);
  elements.setupPanel.addEventListener("click", selectSetupChoice);
  elements.actionDialogCancel.addEventListener("click", closeActionDialog);
  elements.actionDialog.addEventListener("cancel", (event) => { event.preventDefault(); closeActionDialog(); });
  elements.actionDialog.addEventListener("close", () => { ui.actionDialogMode = null; });
  elements.actionDialogPrimary.addEventListener("click", () => submitAction("request"));
  elements.actionDialogAccept.addEventListener("click", () => submitAction("accept"));
  elements.actionDialogReject.addEventListener("click", () => submitAction("reject"));
  elements.actionDialogResign.addEventListener("click", () => submitAction("resign"));
  elements.guideCopyButtons.forEach((button) => button.addEventListener("click", copyGuide));
  elements.localeSelects.forEach((select) => select.addEventListener("change", () => {
    i18n.setLocale(select.value);
    render();
  }));
}

bindEvents();
render();
if (ui.setupOpen) document.querySelector('[data-color="red"]').focus({ preventScroll: true });
connect();
