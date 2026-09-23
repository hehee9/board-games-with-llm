"use strict";

(() => {
  const catalog = window.REVERSI_I18N;
  const locales = catalog.locales;
  const elements = {
    board: document.querySelector("#reversi-board"),
    rankGutter: document.querySelector("#rank-gutter"),
    fileGutter: document.querySelector("#file-gutter"),
    boardStatus: document.querySelector("#board-status"),
    boardCaption: document.querySelector("#board-caption"),
    statusDot: document.querySelector("#status-dot"),
    revision: document.querySelector("#revision-label"),
    matchId: document.querySelector("#match-id"),
    clockFace: document.querySelector("#clock-face"),
    clockLabel: document.querySelector("#clock-label"),
    clockValue: document.querySelector("#clock-value"),
    clockDetail: document.querySelector("#clock-detail"),
    participants: document.querySelector("#participant-strip"),
    lastMove: document.querySelector("#last-move-value"),
    lastMoveMeta: document.querySelector("#last-move-meta"),
    countBlack: document.querySelector("#count-black"),
    countWhite: document.querySelector("#count-white"),
    moveCount: document.querySelector("#move-count"),
    moveList: document.querySelector("#move-list"),
    emptyHistory: document.querySelector("#empty-history"),
    guide: document.querySelector("#guide-section"),
    connection: document.querySelector("#connection-value"),
    live: document.querySelector("#live-indicator"),
    error: document.querySelector("#error-copy"),
    setup: document.querySelector("#setup-dialog"),
    setupForm: document.querySelector("#setup-form"),
    setupError: document.querySelector("#setup-error"),
    setupStart: document.querySelector("#setup-start-button"),
    setupColorFields: document.querySelector("#human-color-fields"),
    action: document.querySelector("#action-dialog"),
    actionEyebrow: document.querySelector("#action-eyebrow"),
    actionHeading: document.querySelector("#action-heading"),
    actionDescription: document.querySelector("#action-description"),
    actionError: document.querySelector("#action-error"),
    actionCancel: document.querySelector("#action-cancel"),
    actionReject: document.querySelector("#action-reject"),
    actionAccept: document.querySelector("#action-accept"),
    actionConfirm: document.querySelector("#action-confirm"),
    takebackButton: document.querySelector("#takeback-button"),
    resignButton: document.querySelector("#resign-button"),
    newGameButton: document.querySelector("#new-game-button"),
  };
  let locale = _initialLocale();
  let snapshot = null;
  let eventSource = null;
  let selectedMode = "human_vs_llm";
  let selectedColor = "black";
  let focusedSquare = "A1";
  let actionType = null;
  let actionFocusTarget = null;
  let setupFocusTarget = null;
  let autoResponseKey = null;

  function _initialLocale() {
    const saved = localStorage.getItem("llm-reversi-locale");
    if (locales.includes(saved)) return saved;
    const preferred = navigator.languages || [navigator.language];
    for (const language of preferred) {
      const exact = locales.find((candidate) => candidate.toLowerCase() === language.toLowerCase());
      if (exact) return exact;
      const subtags = language.toLowerCase().split("-");
      const base = subtags[0];
      if (base === "zh") {
        if (subtags[1] === "hant" || ["tw", "hk", "mo"].includes(subtags[1])) return "zh-Hant";
        if (subtags[1] === "hans") return "zh-Hans";
      }
      const matchingBase = locales.find((candidate) => candidate.split("-")[0].toLowerCase() === base);
      if (matchingBase) return matchingBase;
    }
    return "en";
  }

  function _translate(key, values = {}) {
    let message = catalog.messages[locale][key] ?? catalog.messages.en[key] ?? key;
    for (const [name, value] of Object.entries(values)) {
      message = message.replaceAll("{" + name + "}", String(value));
    }
    return message;
  }

  function _applyLanguage() {
    document.documentElement.lang = locale;
    document.title = _translate("workspace.aria");
    for (const element of document.querySelectorAll("[data-i18n]")) {
      element.textContent = _translate(element.dataset.i18n);
    }
    const connectionState = elements.connection.dataset.state || "connecting";
    const connectionLabel = _translate("connection." + connectionState);
    elements.connection.textContent = connectionLabel;
    elements.live.textContent = connectionLabel;
    for (const element of document.querySelectorAll("[data-i18n-aria-label]")) {
      element.setAttribute("aria-label", _translate(element.dataset.i18nAriaLabel));
    }
    for (const element of document.querySelectorAll("[data-i18n-placeholder]")) {
      element.setAttribute("placeholder", _translate(element.dataset.i18nPlaceholder));
    }
    for (const select of document.querySelectorAll("[data-locale-select]")) {
      select.value = locale;
    }
    if (snapshot) _renderSnapshot(snapshot, true);
    else elements.revision.textContent = _translate("meta.revision") + " 0";
    _renderActionDialog();
  }

  function _setLocale(value) {
    if (!locales.includes(value)) return;
    locale = value;
    localStorage.setItem("llm-reversi-locale", locale);
    _applyLanguage();
  }

  function _apiError(code) {
    const error = new Error(code);
    error.code = code;
    return error;
  }

  async function _request(path, payload) {
    let response;
    try {
      response = await fetch(path, {
        method: payload === undefined ? "GET" : "POST",
        headers: payload === undefined ? undefined : { "Content-Type": "application/json" },
        body: payload === undefined ? undefined : JSON.stringify(payload),
      });
    } catch {
      throw _apiError("network");
    }
    let body;
    try {
      body = await response.json();
    } catch {
      throw _apiError("server");
    }
    if (!response.ok) {
      const code = body?.detail?.code;
      throw _apiError(typeof code === "string" ? code : "server");
    }
    if (!body || typeof body !== "object") throw _apiError("server");
    return body;
  }

  function _errorText(error) {
    return _translate("error." + (error.code ?? "server"));
  }

  function _showError(error) {
    elements.error.textContent = _errorText(error);
    elements.error.hidden = false;
    elements.connection.textContent = _translate("connection.error");
    elements.live.textContent = _translate("connection.error");
    elements.connection.dataset.state = "error";
    elements.statusDot.dataset.state = "error";
  }

  function _clearError() {
    elements.error.textContent = "";
    elements.error.hidden = true;
  }

  function _playerName(color) {
    const player = snapshot?.players?.[color];
    return player?.name || _translate("clock." + color);
  }

  function _boardSquares() {
    const ranks = document.createDocumentFragment();
    const files = document.createDocumentFragment();
    for (let row = 1; row <= 8; row += 1) {
      const rank = document.createElement("span");
      rank.className = "gutter-label";
      rank.textContent = String(row);
      ranks.append(rank);
    }
    for (const file of "ABCDEFGH") {
      const column = document.createElement("span");
      column.className = "gutter-label";
      column.textContent = file;
      files.append(column);
    }
    elements.rankGutter.replaceChildren(ranks);
    elements.fileGutter.replaceChildren(files);
  }

  function _renderBoard() {
    const hadFocus = elements.board.contains(document.activeElement);
    if (hadFocus) focusedSquare = document.activeElement.dataset.square;
    const discs = snapshot?.discs ?? {};
    const legalMoves = new Set(snapshot?.legal_moves ?? []);
    const lastMove = snapshot?.last_move;
    const flipped = new Set(lastMove?.flipped ?? []);
    const humanCanMove = Boolean(
      snapshot
      && snapshot.status === "active"
      && snapshot.game_mode === "human_vs_llm"
      && snapshot.turn === "human"
      && snapshot.takeback?.state !== "pending",
    );
    const squares = document.createDocumentFragment();
    let initialTabStopAssigned = false;
    for (let row = 1; row <= 8; row += 1) {
      for (const file of "ABCDEFGH") {
        const coordinate = file + row;
        const discColor = discs[coordinate];
        const isLegal = legalMoves.has(coordinate);
        const button = document.createElement("button");
        button.type = "button";
        button.className = "square";
        button.dataset.square = coordinate;
        button.setAttribute("role", "gridcell");
        button.setAttribute("aria-disabled", String(!(humanCanMove && isLegal)));
        button.setAttribute("aria-pressed", String(Boolean(discColor)));
        const label = discColor
          ? _translate(discColor === "black" ? "aria.squareBlack" : "aria.squareWhite", { square: coordinate })
          : _translate("aria.squareEmpty", { square: coordinate });
        const annotations = [];
        if (isLegal) {
          button.classList.add("is-legal");
          annotations.push(_translate("aria.legal"));
        }
        if (coordinate === lastMove?.move) {
          button.classList.add("is-last-move");
          annotations.push(_translate("aria.lastMove"));
        }
        if (flipped.has(coordinate)) {
          button.classList.add("is-flipped");
          annotations.push(_translate("aria.flipped"));
        }
        button.setAttribute("aria-label", annotations.length ? label + ", " + annotations.join(", ") : label);
        const useTabStop = coordinate === focusedSquare || (!initialTabStopAssigned && !hadFocus);
        button.tabIndex = useTabStop ? 0 : -1;
        if (useTabStop) initialTabStopAssigned = true;
        if (discColor) {
          button.classList.add("has-disc");
          const disc = document.createElement("span");
          disc.className = "disc stone-" + discColor;
          disc.setAttribute("aria-hidden", "true");
          button.append(disc);
        }
        squares.append(button);
      }
    }
    elements.board.replaceChildren(squares);
    if (hadFocus) elements.board.querySelector('[data-square="' + focusedSquare + '"]')?.focus();
    if (!elements.rankGutter.childElementCount) _boardSquares();
  }

  function _setStatus(text, state = "waiting") {
    elements.boardStatus.textContent = text;
    elements.statusDot.dataset.state = state;
  }

  function _renderParticipants() {
    if (!snapshot?.players || !Object.keys(snapshot.players).length) {
      elements.participants.replaceChildren();
      return;
    }
    const children = [];
    for (const color of ["black", "white"]) {
      const player = snapshot.players[color];
      const item = document.createElement("div");
      item.className = "participant";
      item.dataset.active = String(snapshot.status === "active" && snapshot.to_play === color);
      const colorLabel = document.createElement("span");
      colorLabel.className = "participant-color";
      const swatch = document.createElement("i");
      swatch.className = "disc-swatch stone-" + color;
      swatch.setAttribute("aria-hidden", "true");
      colorLabel.append(swatch, document.createTextNode(_translate("clock." + color)));
      const name = document.createElement("strong");
      name.className = "participant-name";
      const nameKey = player.actor === "human"
        ? "participant.you"
        : player.actor === "llm"
          ? "participant.llm"
          : "clock." + color;
      name.textContent = player.name || _translate(nameKey);
      item.append(colorLabel, name);
      children.push(item);
    }
    elements.participants.replaceChildren(...children);
  }

  function _renderClock() {
    if (!snapshot || snapshot.status === "setup") {
      elements.clockFace.dataset.tone = "terminal";
      elements.clockLabel.textContent = _translate("clock.setup.label");
      elements.clockValue.textContent = _translate("clock.setup.value");
      elements.clockDetail.textContent = _translate("clock.setup.detail");
      return;
    }
    if (snapshot.status === "finished" || snapshot.status === "resigned") {
      const winner = snapshot.winner;
      elements.clockFace.dataset.tone = "terminal";
      elements.clockLabel.textContent = _translate(snapshot.status === "resigned" ? "clock.resigned.label" : "clock.finished.label");
      elements.clockValue.textContent = winner ? _playerName(winner) + " · " + _translate("result.wins") : _translate("result.draw");
      elements.clockDetail.textContent = _translate("clock.black") + " " + snapshot.counts.black + " · " + _translate("clock.white") + " " + snapshot.counts.white;
      return;
    }
    const color = snapshot.to_play;
    const actor = snapshot.turn;
    elements.clockFace.dataset.tone = actor === "human" ? "human" : "llm";
    elements.clockLabel.textContent = _translate("clock.turn.label");
    elements.clockValue.textContent = _playerName(color);
    elements.clockDetail.textContent = actor === "human"
      ? _translate("clock.human")
      : actor === "llm"
        ? _translate("clock.llm")
        : _translate("status.cliTurn", { color: _translate("clock." + color) });
  }

  function _renderLastMove() {
    const move = snapshot?.last_move;
    if (!move) {
      elements.lastMove.textContent = _translate("lastMove.empty");
      elements.lastMoveMeta.textContent = "";
      return;
    }
    const color = _translate("clock." + move.color);
    elements.lastMove.textContent = _translate("lastMove.played", { color, move: move.move });
    elements.lastMoveMeta.textContent = move.flipped.length
      ? _translate("lastMove.flipped", { squares: move.flipped.join(", ") })
      : "";
  }

  function _renderHistory() {
    const moves = snapshot?.move_history ?? [];
    elements.moveCount.textContent = _translate("history.count", { count: moves.length });
    elements.emptyHistory.hidden = moves.length > 0;
    const fragment = document.createDocumentFragment();
    for (const move of moves) {
      const item = document.createElement("li");
      const number = document.createElement("span");
      number.className = "move-number";
      number.textContent = String(move.ply).padStart(2, "0");
      const color = document.createElement("span");
      color.className = "move-color";
      color.textContent = _translate("clock." + move.color);
      const coordinate = document.createElement("strong");
      coordinate.className = "move-square";
      coordinate.textContent = move.move;
      const count = document.createElement("span");
      count.className = "move-flipped";
      count.textContent = "+" + move.flipped.length;
      item.setAttribute("aria-label", number.textContent + " · " + color.textContent + " · " + coordinate.textContent + " · " + count.textContent);
      item.append(number, color, coordinate, count);
      fragment.append(item);
    }
    elements.moveList.replaceChildren(fragment);
  }

  function _turnActions() {
    const inHumanMode = snapshot?.game_mode === "human_vs_llm";
    const active = snapshot?.status === "active";
    const pending = snapshot?.takeback?.state === "pending";
    elements.takebackButton.hidden = !inHumanMode;
    elements.resignButton.hidden = !inHumanMode;
    elements.takebackButton.disabled = !active || pending || !snapshot.move_history.some((move) => move.actor === "human");
    elements.resignButton.disabled = !active;
  }

  function _renderGuide() {
    const visible = snapshot?.game_mode === "cli_vs_cli";
    elements.guide.hidden = !visible;
    if (!visible) return;
    for (const color of ["black", "white"]) {
      const name = _playerName(color);
      document.querySelector('[data-guide-title="' + color + '"]').textContent = name;
      document.querySelector('[data-guide-command="' + color + '"]').textContent = [
        "reversi --color " + color + " status",
        "reversi --color " + color + " wait",
        "reversi --color " + color + " move <square>",
        "reversi --color " + color + " takeback request|accept|reject",
        "reversi --color " + color + " resign",
      ].join("\n");
      document.querySelector('[data-guide-prompt="' + color + '"]').textContent = _translate("guide." + color + "Prompt");
    }
  }

  function _renderActionDialog() {
    if (!actionType) return;
    elements.actionReject.hidden = actionType !== "takeback-response";
    elements.actionAccept.hidden = actionType !== "takeback-response";
    elements.actionConfirm.hidden = actionType === "takeback-response";
    elements.actionCancel.hidden = actionType === "takeback-response";
    elements.actionError.hidden = true;
    if (actionType === "takeback-request") {
      elements.actionEyebrow.textContent = _translate("toolbar.takeback");
      elements.actionHeading.textContent = _translate("dialog.takebackHeading");
      elements.actionDescription.textContent = _translate("dialog.takebackDescription");
      elements.actionConfirm.textContent = _translate("dialog.takebackConfirm");
    } else if (actionType === "takeback-response") {
      elements.actionEyebrow.textContent = _translate("toolbar.takeback");
      elements.actionHeading.textContent = _translate("dialog.takebackResponseHeading");
      elements.actionDescription.textContent = _translate("dialog.takebackResponseDescription");
    } else if (actionType === "resign") {
      elements.actionEyebrow.textContent = _translate("toolbar.resign");
      elements.actionHeading.textContent = _translate("dialog.resignHeading");
      elements.actionDescription.textContent = _translate("dialog.resignDescription");
      elements.actionConfirm.textContent = _translate("dialog.resignConfirm");
    }
  }

  function _renderSnapshot(nextSnapshot, force = false) {
    if (!force && snapshot && Number(nextSnapshot.revision) < Number(snapshot.revision)) return;
    snapshot = nextSnapshot;
    elements.matchId.textContent = snapshot.game_id ? _translate("meta.game") + " " + snapshot.game_id.slice(0, 8) : "—";
    elements.revision.textContent = _translate("meta.revision") + " " + snapshot.revision;
    elements.countBlack.textContent = String(snapshot.counts.black);
    elements.countWhite.textContent = String(snapshot.counts.white);
    _renderBoard();
    _renderParticipants();
    _renderClock();
    _renderLastMove();
    _renderHistory();
    _turnActions();
    _renderGuide();
    _clearError();

    let status;
    if (snapshot.status === "setup") status = _translate("status.setup");
    else if (snapshot.status === "finished") status = _translate("status.finished");
    else if (snapshot.status === "resigned") status = _translate("status.resigned");
    else if (snapshot.takeback?.state === "pending") status = _translate("status.pending");
    else if (snapshot.auto_passed_color) status = _translate("board.passNotice", { color: _translate("clock." + snapshot.auto_passed_color) });
    else if (snapshot.turn === "human") status = _translate("status.yourTurn");
    else if (snapshot.turn === "llm") status = _translate("status.opponentTurn");
    else status = _translate("status.cliTurn", { color: _translate("clock." + snapshot.turn) });
    _setStatus(status, snapshot.status === "active" ? "connected" : "waiting");
    elements.boardCaption.textContent = status;

    if (snapshot.status === "setup" && !elements.setup.open) _openSetup(false);
    if (snapshot.status !== "setup" && elements.setup.open) elements.setup.close();
    const pending = snapshot.takeback?.state === "pending";
    if (pending && snapshot.game_mode === "human_vs_llm" && snapshot.takeback.requester !== "human") {
      const requestKey = snapshot.game_id + ":" + snapshot.takeback.target_ply;
      if (requestKey !== autoResponseKey) {
        autoResponseKey = requestKey;
        _openAction("takeback-response");
      }
    } else if (!pending && actionType === "takeback-response") {
      _closeAction();
    }
  }

  function _setConnection(state) {
    const key = state === "connected" ? "connected" : state === "connecting" ? "connecting" : "disconnected";
    elements.connection.textContent = _translate("connection." + key);
    elements.live.textContent = _translate("connection." + key);
    elements.connection.dataset.state = state;
    elements.statusDot.dataset.state = state === "connected" ? "connected" : state === "connecting" ? "waiting" : "disconnected";
    elements.live.dataset.state = state === "connected" ? "connected" : state === "connecting" ? "waiting" : "error";
    if (state === "disconnected") {
      elements.boardStatus.textContent = _translate("error.network");
      elements.error.textContent = _translate("error.network");
      elements.error.hidden = false;
    } else if (state === "connected" && elements.error.textContent === _translate("error.network")) {
      _clearError();
    }
  }

  function _syncSetupControls() {
    for (const button of document.querySelectorAll("[data-mode]")) {
      const selected = button.dataset.mode === selectedMode;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    }
    for (const button of document.querySelectorAll("[data-color]")) {
      const selected = button.dataset.color === selectedColor;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    }
    elements.setupColorFields.hidden = selectedMode !== "human_vs_llm";
  }

  function _openSetup(fromButton = true) {
    if (elements.setup.open) {
      _syncSetupControls();
      return;
    }
    if (fromButton) setupFocusTarget = document.activeElement;
    elements.setupError.hidden = true;
    if (snapshot?.status !== "setup") {
      selectedMode = snapshot?.game_mode ?? selectedMode;
      selectedColor = snapshot?.human_color ?? selectedColor;
      document.querySelector("#black-name").value = snapshot?.players?.black?.name ?? "";
      document.querySelector("#white-name").value = snapshot?.players?.white?.name ?? "";
    }
    _syncSetupControls();
    elements.setup.showModal();
    document.querySelector('[data-mode="' + selectedMode + '"]')?.focus();
  }

  function _openAction(type) {
    actionType = type;
    actionFocusTarget = document.activeElement;
    _renderActionDialog();
    if (!elements.action.open) elements.action.showModal();
    (type === "takeback-response" ? elements.actionAccept : elements.actionConfirm).focus();
  }

  function _closeAction() {
    if (!elements.action.open) {
      actionType = null;
      return;
    }
    actionType = null;
    elements.action.close();
    actionFocusTarget?.focus();
    actionFocusTarget = null;
  }

  async function _runAction(action) {
    elements.actionError.hidden = true;
    let path;
    let payload;
    if (actionType === "takeback-request") {
      path = "/api/human/takeback";
      payload = { action: "request" };
    } else if (actionType === "takeback-response") {
      path = "/api/human/takeback";
      payload = { action };
    } else {
      path = "/api/human/resign";
    }
    const button = action === "accept" ? elements.actionAccept : action === "reject" ? elements.actionReject : elements.actionConfirm;
    button.disabled = true;
    try {
      const next = await _request(path, payload);
      _renderSnapshot(next);
      _closeAction();
    } catch (error) {
      elements.actionError.textContent = _errorText(error);
      elements.actionError.hidden = false;
    } finally {
      button.disabled = false;
    }
  }

  async function _placeHumanMove(move) {
    try {
      const next = await _request("/api/human/moves", { move, wait: false });
      _renderSnapshot(next);
    } catch (error) {
      _showError(error);
    }
  }

  async function _startGame(event) {
    event.preventDefault();
    elements.setupError.hidden = true;
    elements.setupStart.disabled = true;
    const payload = {
      game_mode: selectedMode,
      human_color: selectedMode === "human_vs_llm" ? selectedColor : null,
      black_name: document.querySelector("#black-name").value.trim() || null,
      white_name: document.querySelector("#white-name").value.trim() || null,
    };
    try {
      const next = await _request("/api/games", payload);
      _renderSnapshot(next);
      elements.setup.close();
      setupFocusTarget?.focus();
      setupFocusTarget = null;
    } catch (error) {
      elements.setupError.textContent = _errorText(error);
      elements.setupError.hidden = false;
    } finally {
      elements.setupStart.disabled = false;
    }
  }

  function _moveFocus(event) {
    const current = event.target.closest(".square");
    if (!current) return;
    const offsets = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0] };
    const offset = offsets[event.key];
    if (!offset) return;
    event.preventDefault();
    const currentSquare = current.dataset.square;
    const x = currentSquare.charCodeAt(0) - 65;
    const y = Number(currentSquare.slice(1)) - 1;
    const nextX = Math.max(0, Math.min(7, x + offset[0]));
    const nextY = Math.max(0, Math.min(7, y + offset[1]));
    focusedSquare = String.fromCharCode(65 + nextX) + (nextY + 1);
    elements.board.querySelector('[data-square="' + focusedSquare + '"]')?.focus();
  }

  async function _copyGuide(event) {
    const button = event.target.closest("[data-copy-kind]");
    if (!button) return;
    const color = button.dataset.copyColor;
    const kind = button.dataset.copyKind;
    const text = kind === "command"
      ? document.querySelector('[data-guide-command="' + color + '"]').textContent
      : _translate("guide." + color + "Prompt");
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = _translate("guide.copied");
      window.setTimeout(() => {
        button.textContent = _translate(kind === "command" ? "guide.copyCommand" : "guide.copyPrompt");
      }, 1400);
    } catch {
      _showError(_apiError("server"));
      elements.error.textContent = _translate("guide.copyFailed");
    }
  }

  async function _boot() {
    _applyLanguage();
    _boardSquares();
    document.querySelectorAll("[data-locale-select]").forEach((select) => {
      select.addEventListener("change", () => _setLocale(select.value));
    });
    document.querySelectorAll("[data-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedMode = button.dataset.mode;
        _syncSetupControls();
      });
    });
    document.querySelectorAll("[data-color]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedColor = button.dataset.color;
        _syncSetupControls();
      });
    });
    elements.newGameButton.addEventListener("click", () => _openSetup());
    elements.takebackButton.addEventListener("click", () => _openAction("takeback-request"));
    elements.resignButton.addEventListener("click", () => _openAction("resign"));
    elements.setupForm.addEventListener("submit", _startGame);
    elements.setup.addEventListener("cancel", (event) => {
      if (snapshot?.status === "setup") event.preventDefault();
    });
    elements.setup.addEventListener("close", () => {
      if (snapshot?.status !== "setup") {
        setupFocusTarget?.focus();
        setupFocusTarget = null;
      }
    });
    elements.actionCancel.addEventListener("click", _closeAction);
    elements.actionConfirm.addEventListener("click", () => _runAction(actionType === "resign" ? "resign" : "request"));
    elements.actionAccept.addEventListener("click", () => _runAction("accept"));
    elements.actionReject.addEventListener("click", () => _runAction("reject"));
    elements.action.addEventListener("cancel", (event) => {
      if (actionType === "takeback-response") event.preventDefault();
      else actionType = null;
    });
    elements.action.addEventListener("close", () => {
      if (!actionType) {
        actionFocusTarget?.focus();
        actionFocusTarget = null;
      }
    });
    elements.board.addEventListener("click", (event) => {
      const button = event.target.closest(".square");
      if (!button || button.getAttribute("aria-disabled") === "true") return;
      focusedSquare = button.dataset.square;
      _placeHumanMove(focusedSquare);
    });
    elements.board.addEventListener("keydown", _moveFocus);
    elements.guide.addEventListener("click", _copyGuide);

    try {
      const initial = await _request("/api/state");
      _renderSnapshot(initial);
      _setConnection("connected");
    } catch (error) {
      _showError(error);
      _openSetup(false);
    }
    eventSource = new EventSource("/api/events");
    eventSource.onopen = () => _setConnection("connected");
    eventSource.onerror = () => _setConnection("disconnected");
    eventSource.onmessage = (event) => {
      try {
        _renderSnapshot(JSON.parse(event.data));
        _setConnection("connected");
      } catch {
        _showError(_apiError("server"));
      }
    };
  }

  _boot();
})();
