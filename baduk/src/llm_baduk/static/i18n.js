/**
 * @file LLM Baduk 정적 다국어 기반
 * @description 바둑 작업대 문구와 서버 오류 코드를 여덟 언어로 제공합니다.
 */

const SUPPORTED_LOCALES = ["en", "ko", "zh-Hans", "zh-Hant", "ja", "es", "fr", "de"];
const LANGUAGE_OPTIONS = [
  ["en", "English"],
  ["ko", "한국어"],
  ["zh-Hans", "简体中文"],
  ["zh-Hant", "繁體中文"],
  ["ja", "日本語"],
  ["es", "Español"],
  ["fr", "Français"],
  ["de", "Deutsch"],
];
const STORAGE_KEY = "llm-baduk-locale";

const ENGLISH_CATALOG = {
  "meta.title": "LLM Baduk · Local Baduk Workbench",
  "meta.description": "A local baduk workbench where a browser human and a CLI LLM share one game.",
  "brand.tagline": "LOCAL BADUK · SHARED BOARD",
  "match.none": "No game",
  "match.game": "Game {id}",
  "toolbar.newGame": "New game",
  "toolbar.actions": "Game actions",
  "toolbar.takeback": "Take back",
  "toolbar.resign": "Resign",
  "language.label": "Language",
  "workspace.aria": "Baduk workbench",
  "board.section": "BOARD",
  "board.currentGame": "Current game",
  "board.waiting": "Waiting for server state",
  "board.chooseColor": "Choose a color and board size for a new game",
  "board.caption.human": "{color} · Human turn · {size}×{size}",
  "board.caption.llm": "{color} · LLM turn · {size}×{size}",
  "board.caption.scoring": "Score review · {size}×{size}",
  "board.caption.terminal": "{color} · Game over · {size}×{size}",
  "board.caption.cli": "{black} · Black vs {white} · {size}×{size}",
  "board.aria": "Baduk board",
  "board.controls": "Board controls",
  "board.pass": "Pass",
  "board.revisionInitial": "REV 0",
  "board.revision": "REV {revision}",
  "turn.heading": "ACTIVE TURN",
  "live.connected": " LIVE",
  "live.waiting": " WAIT",
  "clock.setup.label": "GAME READY",
  "clock.setup.value": "—",
  "clock.setup.detail": "Choose a color and size to begin.",
  "clock.error.label": "REQUEST ERROR",
  "clock.error.value": "CHECK",
  "clock.error.detail": "Review the connection status and error message.",
  "clock.disconnected.label": "RECONNECTING",
  "clock.disconnected.value": "WAIT",
  "clock.disconnected.detail": "The event stream will reconnect automatically.",
  "clock.requestError.label": "REQUEST ERROR",
  "clock.requestError.value": "RETRY",
  "clock.requestError.detail": "Review the error message, then choose an action again.",
  "clock.scoring.label": "SCORE REVIEW",
  "clock.scoring.value": "MARK",
  "clock.scoring.detail": "Mark dead or seki groups, then accept the displayed score.",
  "clock.finished.label": "FINISHED",
  "clock.finished.detail": "The score has been accepted by both sides.",
  "clock.finished.cliDetail": "Black {black} and White {white} accepted the score.",
  "clock.draw.label": "DRAW",
  "clock.terminal.value": "END",
  "clock.human.label": "HUMAN TURN",
  "clock.human.value": "YOUR TURN",
  "clock.human.detail": "Place a {color} stone or pass.",
  "clock.llm.label": "LLM TURN",
  "clock.llm.value": "LLM TURN",
  "clock.llm.detail": "Waiting for the {color} move from the CLI.",
  "clock.cli.label": "CLI TURN",
  "clock.cli.detail": "Waiting for the {color} move from the CLI.",
  "clock.takeback.label": "TAKEBACK",
  "clock.takeback.outgoingValue": "WAIT",
  "clock.takeback.incomingValue": "REPLY",
  "clock.takeback.outgoingDetail": "Waiting for the LLM to answer your request.",
  "clock.takeback.incomingDetail": "The LLM asks to undo the latest move. Choose a response.",
  "clock.resigned.label": "RESIGNATION",
  "clock.resigned.value": "END",
  "clock.resigned.detail": "{actor} resigned. The game is over.",
  "status.connectionError": "Server request error · Review the message below.",
  "status.connecting": "Connecting to the server.",
  "status.disconnected": "The server connection was lost · Reconnecting automatically.",
  "status.requestError": "Request error · Review the message below and try again.",
  "status.setup": "Choose a color and board size to start a new game.",
  "status.human": "Your turn. Choose an open intersection.",
  "status.llm": "The LLM turn is active. Waiting for the CLI response.",
  "status.cliBlack": "{name} is to play Black. Waiting for the CLI response.",
  "status.cliWhite": "{name} is to play White. Waiting for the CLI response.",
  "status.scoring": "Score review. Mark groups or accept the displayed score.",
  "status.finished": "Finished · {result}",
  "status.draw": "Draw · {result}",
  "status.takebackHuman": "Takeback requested · Waiting for the LLM response.",
  "status.takebackLlm": "The LLM requested a takeback · Choose a response.",
  "status.resigned": "{actor} resigned · The game is over.",
  "lastMove.heading": "LAST MOVE",
  "lastMove.empty": "No moves yet",
  "lastMove.waiting": "Waiting for the first move",
  "lastMove.meta": "{actor} · {color} · captured {captured}",
  "history.heading": "MOVE HISTORY",
  "history.count": "{count} moves",
  "history.aria": "Current game move history",
  "history.empty": "Moves will appear here after the game starts.",
  "history.itemAria": "Ply {ply}: {move}, {color}, {actor}",
  "connection.aria": "Connection status",
  "connection.label": "Connection",
  "connection.connecting": "Checking",
  "connection.connected": "Connected",
  "connection.disconnected": "Reconnecting",
  "connection.error": "Request error",
  "score.heading": "SCORE",
  "score.live": "LIVE",
  "score.review": "REVIEW",
  "score.final": "FINAL",
  "score.black": "Black",
  "score.white": "White",
  "score.territoryBlack": "B territory",
  "score.territoryWhite": "W territory",
  "score.komi": "Komi",
  "score.prisoners": "Prisoners",
  "score.waiting": "Score details appear after two passes.",
  "score.modeLabel": "MARK GROUPS",
  "score.dead": "Dead stones",
  "score.seki": "Seki groups",
  "score.accept": "Accept score",
  "score.resume": "Resume play",
  "score.accepted": "Human {human} · LLM {llm}",
  "score.acceptedCli": "Black {black} · White {white}",
  "score.acceptedShort": "accepted",
  "score.pendingShort": "waiting",
  "score.breakdown": "Territory: B {black} · W {white}",
  "setup.eyebrow": "NEW MATCH · CONFIGURE THE BOARD",
  "setup.heading": "Configure a new game",
  "setup.description": "Choose your stones and board size. The LLM plays from a separate CLI.",
  "setup.modeLabel": "Game mode",
  "setup.modeAria": "Game mode selection",
  "setup.mode.human.label": "Human vs AI",
  "setup.mode.human.detail": "Play one side in the browser",
  "setup.mode.cli.label": "AI vs AI",
  "setup.mode.cli.detail": "Watch two CLI sessions play",
  "setup.colorLabel": "Your stones",
  "setup.groupAria": "Human color selection",
  "setup.sizeLabel": "Board size",
  "setup.sizeAria": "Board size selection",
  "setup.black.label": "Play Black",
  "setup.black.detail": "You move first",
  "setup.white.label": "Play White",
  "setup.white.detail": "The LLM moves first",
  "setup.size.default": "Standard",
  "setup.size.medium": "Medium",
  "setup.size.small": "Quick game",
  "setup.start": "Start game",
  "setup.namesLabel": "AI names",
  "setup.blackName": "Black AI",
  "setup.whiteName": "White AI",
  "setup.namePlaceholder": "Optional name",
  "takeback.dialog.eyebrow": "GAME ACTION · TAKEBACK",
  "takeback.request.heading": "Request a takeback?",
  "takeback.request.description": "Ask the LLM to take back {plies} move(s), including ply {target}.",
  "takeback.request.cancel": "Cancel",
  "takeback.request.confirm": "Request",
  "takeback.response.heading": "The LLM requests a takeback",
  "takeback.response.description": "The request takes back {plies} move(s), including ply {target}.",
  "takeback.response.reject": "Reject",
  "takeback.response.accept": "Accept",
  "takeback.aria": "Takeback action dialog",
  "resign.dialog.eyebrow": "GAME ACTION · RESIGN",
  "resign.heading": "Resign this game?",
  "resign.description": "Resigning ends the game and awards the win to the other side.",
  "resign.confirm": "Resign",
  "resign.aria": "Resignation confirmation dialog",
  "color.black": "Black",
  "color.white": "White",
  "actor.human": "Human",
  "actor.llm": "LLM",
  "player.blackDefault": "Black AI",
  "player.whiteDefault": "White AI",
  "point.name": "{point}",
  "point.stone": "{point}, {color} stone",
  "point.empty": "{point}, empty intersection",
  "point.legal": "legal move",
  "confirm.newGame": "Discard the current game and start a new one?",
  "guide.aria": "AI connection guide",
  "guide.summary": "Connect the two AI sessions",
  "guide.description": "Run one independent CLI session for each color. This browser only watches the shared game.",
  "guide.commandLabel": "Commands",
  "guide.promptLabel": "Session prompt",
  "guide.copyCommand": "Copy commands",
  "guide.copyPrompt": "Copy prompt",
  "guide.copied": "Copied",
  "guide.copyError": "Could not copy the text. Select and copy it manually.",
  "error.generic": "The server returned an unexpected error. Try again.",
  "error.connect": "Could not connect to the server.",
  "error.state": "Could not read the server state.",
  "error.move": "Could not send the move.",
  "error.start": "Could not start a new game.",
  "error.score": "Could not update the score.",
  "error.takeback": "Could not send the takeback action.",
  "error.resign": "Could not resign the game.",
  "error.noGame": "No game is in progress. Start a game first.",
  "error.gameOver": "The game is already over.",
  "error.wrongTurn": "It is not your side's turn.",
  "error.illegalMove": "That move is not legal: {move}",
  "error.invalidColor": "Choose Black or White to start the game.",
  "error.invalidBoardSize": "Choose a 9×9, 13×13, or 19×19 board.",
  "error.takebackUnavailable": "A takeback is not available right now.",
  "error.takebackPending": "A takeback request is already waiting for a response.",
  "error.noPendingTakeback": "There is no takeback request to answer.",
  "error.resignUnavailable": "Resignation is not available right now.",
  "error.scoreNotScoring": "Score actions are available during score review.",
  "error.pointRequired": "Choose a stone group to mark.",
  "error.invalidPoint": "That intersection is not available for this action.",
  "error.staleRevision": "The score changed. Review the current board and try again.",
  "error.scoreRevisionRequired": "The displayed revision is required to accept a score.",
  "error.invalidRevision": "The revision must be a non-negative number.",
  "error.alreadyAccepted": "Your score is already accepted. Wait for the other side.",
  "error.invalidAction": "That game action is not available right now.",
  "error.gameExists": "A game is already in progress.",
};

const CATALOG_OVERRIDES = {
  ko: {
    "clock.scoring.detail": "사석이나 빅인 돌 무리를 표시한 뒤 현재 점수를 수락하세요.", "status.scoring": "계가 검토 중입니다. 돌 무리를 표시하거나 현재 점수를 수락하세요.", "score.modeLabel": "돌 표시", "score.seki": "빅인 돌 무리", "error.pointRequired": "표시할 돌 무리를 고르세요.",
  },
  "zh-Hans": { "meta.title": "LLM Baduk · 本地围棋工作台", "brand.tagline": "本地对局 · 人类 × LLM", "match.none": "暂无对局", "match.game": "对局 {id}", "toolbar.newGame": "新对局", "toolbar.takeback": "悔棋", "toolbar.resign": "认输", "language.label": "语言", "workspace.aria": "围棋工作台", "board.section": "棋盘", "board.currentGame": "当前对局", "board.chooseColor": "选择棋色和棋盘大小开始新对局", "board.caption.human": "{color} · 人类回合 · {size}×{size}", "board.caption.llm": "{color} · LLM 回合 · {size}×{size}", "board.caption.scoring": "计分复核 · {size}×{size}", "board.caption.terminal": "{color} · 对局结束 · {size}×{size}", "board.aria": "围棋棋盘", "board.controls": "棋盘操作", "board.pass": "停着", "turn.heading": "当前回合", "clock.setup.label": "对局准备", "clock.setup.detail": "选择棋色和大小开始。", "clock.human.label": "人类回合", "clock.human.value": "轮到你", "clock.human.detail": "落下{color}棋或停着。", "clock.llm.label": "LLM 回合", "clock.llm.value": "LLM 回合", "clock.llm.detail": "等待 CLI 发送{color}棋。", "clock.scoring.label": "计分复核", "clock.scoring.value": "标记", "clock.scoring.detail": "标记死子或双活，然后接受当前分数。", "clock.finished.label": "结束", "clock.draw.label": "和棋", "clock.terminal.value": "结束", "status.setup": "选择棋色和大小开始新对局。", "status.human": "轮到你。选择空的交叉点。", "status.llm": "LLM 回合进行中，等待 CLI 响应。", "status.scoring": "计分复核中。标记棋块或接受当前分数。", "status.finished": "结束 · {result}", "status.draw": "和棋 · {result}", "lastMove.heading": "最近一手", "lastMove.empty": "暂无落子", "lastMove.waiting": "等待第一手", "history.heading": "着手记录", "history.count": "{count} 手", "history.empty": "开始对局后，着手会显示在这里。", "score.heading": "计分", "score.black": "黑", "score.white": "白", "score.territoryBlack": "黑地", "score.territoryWhite": "白地", "score.komi": "贴目", "score.prisoners": "提子", "score.waiting": "双方停着后显示计分详情。", "score.dead": "标记死子", "score.seki": "标记双活", "score.accept": "接受计分", "score.resume": "继续对局", "score.review": "复核", "score.final": "最终", "score.live": "进行中", "score.modeLabel": "标记棋块", "setup.eyebrow": "新对局 · 设置棋盘", "setup.heading": "设置新对局", "setup.description": "选择棋色和大小。LLM 通过独立 CLI 落子。", "setup.colorLabel": "你的棋色", "setup.groupAria": "人类棋色选择", "setup.sizeLabel": "棋盘大小", "setup.sizeAria": "棋盘大小选择", "setup.black.label": "执黑", "setup.black.detail": "你先行", "setup.white.label": "执白", "setup.white.detail": "LLM 先行", "setup.size.default": "标准", "setup.size.medium": "中型", "setup.size.small": "快速对局", "setup.start": "开始对局", "point.stone": "{point}，{color}棋", "point.empty": "{point}，空交叉点", "point.legal": "合法落子", "color.black": "黑", "color.white": "白", "actor.human": "人类", "actor.llm": "LLM", "takeback.request.heading": "请求悔棋？", "takeback.request.cancel": "取消", "takeback.request.confirm": "请求", "takeback.response.heading": "LLM 请求悔棋", "takeback.response.reject": "拒绝", "takeback.response.accept": "接受", "resign.heading": "要认输吗？", "resign.confirm": "认输", "confirm.newGame": "放弃当前对局并开始新对局？", "error.generic": "服务器返回了未预期的错误，请重试。", "error.connect": "无法连接服务器。", "error.state": "无法读取服务器状态。", "error.move": "无法发送落子。", "error.start": "无法开始新对局。", "error.score": "无法更新计分。", "error.takeback": "无法发送悔棋操作。", "error.resign": "无法认输。", "error.noGame": "当前没有对局，请先开始。", "error.gameOver": "对局已经结束。", "error.wrongTurn": "现在不是你的回合。", "error.illegalMove": "此着不合法：{move}", "error.invalidColor": "请选择黑或白。", "error.invalidBoardSize": "请选择 9×9、13×13 或 19×19 棋盘。", "error.takebackUnavailable": "现在不能悔棋。", "error.takebackPending": "已有悔棋请求等待回复。", "error.noPendingTakeback": "没有待处理的悔棋请求。", "error.resignUnavailable": "现在不能认输。", "error.scoreNotScoring": "计分操作仅在计分复核时可用。", "error.pointRequired": "请选择要标记的棋块。", "error.invalidPoint": "此交叉点不能用于该操作。", "error.staleRevision": "计分已变化，请检查当前棋盘后重试。", "error.alreadyAccepted": "你已经接受计分，请等待对方。", "error.invalidAction": "现在不能使用此操作。", "error.gameExists": "已有进行中的对局。" },
  "zh-Hant": { "meta.title": "LLM Baduk · 本地圍棋工作台", "brand.tagline": "本地對局 · 人類 × LLM", "match.none": "沒有對局", "match.game": "對局 {id}", "toolbar.newGame": "新對局", "toolbar.takeback": "悔棋", "toolbar.resign": "認輸", "language.label": "語言", "workspace.aria": "圍棋工作台", "board.section": "棋盤", "board.currentGame": "目前對局", "board.chooseColor": "選擇棋色和棋盤大小開始新對局", "board.caption.human": "{color} · 人類回合 · {size}×{size}", "board.caption.llm": "{color} · LLM 回合 · {size}×{size}", "board.caption.scoring": "計分檢查 · {size}×{size}", "board.caption.terminal": "{color} · 對局結束 · {size}×{size}", "board.aria": "圍棋棋盤", "board.controls": "棋盤操作", "board.pass": "虛手", "turn.heading": "目前回合", "clock.setup.label": "對局準備", "clock.setup.detail": "選擇棋色和大小開始。", "clock.human.label": "人類回合", "clock.human.value": "輪到你", "clock.human.detail": "落下{color}棋或虛手。", "clock.llm.label": "LLM 回合", "clock.llm.value": "LLM 回合", "clock.llm.detail": "等待 CLI 傳送{color}棋。", "clock.scoring.label": "計分檢查", "clock.scoring.value": "標記", "clock.scoring.detail": "標記死子或雙活，然後接受目前分數。", "clock.finished.label": "結束", "clock.draw.label": "和棋", "clock.terminal.value": "結束", "status.setup": "選擇棋色和大小開始新對局。", "status.human": "輪到你。選擇空的交叉點。", "status.llm": "LLM 回合進行中，等待 CLI 回應。", "status.scoring": "計分檢查中。標記棋塊或接受目前分數。", "status.finished": "結束 · {result}", "status.draw": "和棋 · {result}", "lastMove.heading": "最近一手", "lastMove.empty": "尚未落子", "lastMove.waiting": "等待第一手", "history.heading": "著手記錄", "history.count": "{count} 手", "history.empty": "開始對局後，著手會顯示在這裡。", "score.heading": "計分", "score.black": "黑", "score.white": "白", "score.territoryBlack": "黑地", "score.territoryWhite": "白地", "score.komi": "貼目", "score.prisoners": "提子", "score.waiting": "雙方虛手後顯示計分詳情。", "score.dead": "標記死子", "score.seki": "標記雙活", "score.accept": "接受計分", "score.resume": "繼續對局", "score.review": "檢查", "score.final": "最終", "score.live": "進行中", "score.modeLabel": "標記棋塊", "setup.eyebrow": "新對局 · 設定棋盤", "setup.heading": "設定新對局", "setup.description": "選擇棋色和大小。LLM 透過獨立 CLI 落子。", "setup.colorLabel": "你的棋色", "setup.groupAria": "人類棋色選擇", "setup.sizeLabel": "棋盤大小", "setup.sizeAria": "棋盤大小選擇", "setup.black.label": "執黑", "setup.black.detail": "你先行", "setup.white.label": "執白", "setup.white.detail": "LLM 先行", "setup.size.default": "標準", "setup.size.medium": "中型", "setup.size.small": "快速對局", "setup.start": "開始對局", "point.stone": "{point}，{color}棋", "point.empty": "{point}，空交叉點", "point.legal": "合法落子", "color.black": "黑", "color.white": "白", "actor.human": "人類", "actor.llm": "LLM", "takeback.request.heading": "要請求悔棋嗎？", "takeback.request.cancel": "取消", "takeback.request.confirm": "請求", "takeback.response.heading": "LLM 請求悔棋", "takeback.response.reject": "拒絕", "takeback.response.accept": "接受", "resign.heading": "要認輸嗎？", "resign.confirm": "認輸", "confirm.newGame": "放棄目前對局並開始新對局？", "error.generic": "伺服器回傳未預期的錯誤，請重試。", "error.connect": "無法連線伺服器。", "error.state": "無法讀取伺服器狀態。", "error.move": "無法傳送落子。", "error.start": "無法開始新對局。", "error.score": "無法更新計分。", "error.takeback": "無法傳送悔棋操作。", "error.resign": "無法認輸。", "error.noGame": "目前沒有對局，請先開始。", "error.gameOver": "對局已經結束。", "error.wrongTurn": "現在不是你的回合。", "error.illegalMove": "此著不合法：{move}", "error.invalidColor": "請選擇黑或白。", "error.invalidBoardSize": "請選擇 9×9、13×13 或 19×19 棋盤。", "error.takebackUnavailable": "現在不能悔棋。", "error.takebackPending": "已有悔棋請求等待回覆。", "error.noPendingTakeback": "沒有待處理的悔棋請求。", "error.resignUnavailable": "現在不能認輸。", "error.scoreNotScoring": "計分操作只在計分檢查時可用。", "error.pointRequired": "請選擇要標記的棋塊。", "error.invalidPoint": "此交叉點不能用於該操作。", "error.staleRevision": "計分已變更，請檢查目前棋盤後重試。", "error.alreadyAccepted": "你已經接受計分，請等待對方。", "error.invalidAction": "現在不能使用此操作。", "error.gameExists": "已有進行中的對局。" },
  ja: { "meta.title": "LLM Baduk · ローカル囲碁ワークベンチ", "brand.tagline": "ローカル対局 · 人間 × LLM", "match.none": "対局なし", "match.game": "対局 {id}", "toolbar.newGame": "新しい対局", "toolbar.takeback": "待った", "toolbar.resign": "投了", "language.label": "言語", "workspace.aria": "囲碁ワークベンチ", "board.section": "盤", "board.currentGame": "現在の対局", "board.chooseColor": "石の色と盤の大きさを選んで対局を始めます", "board.caption.human": "{color} · 人間の手番 · {size}×{size}", "board.caption.llm": "{color} · LLMの手番 · {size}×{size}", "board.caption.scoring": "整地確認 · {size}×{size}", "board.caption.terminal": "{color} · 対局終了 · {size}×{size}", "board.aria": "囲碁盤", "board.controls": "盤の操作", "board.pass": "パス", "turn.heading": "現在の手番", "clock.setup.label": "対局準備", "clock.setup.detail": "色と大きさを選んで始めます。", "clock.human.label": "人間の手番", "clock.human.value": "あなたの番", "clock.human.detail": "{color}の石を置くかパスします。", "clock.llm.label": "LLMの手番", "clock.llm.value": "LLMの番", "clock.llm.detail": "CLIから{color}の着手を待っています。", "clock.scoring.label": "整地確認", "clock.scoring.value": "印を付ける", "clock.scoring.detail": "死に石またはセキを印し、表示された点数を承認します。", "clock.finished.label": "終了", "clock.draw.label": "引き分け", "clock.terminal.value": "終了", "status.setup": "色と盤の大きさを選んで対局を始めます。", "status.human": "あなたの番です。空いている交点を選んでください。", "status.llm": "LLMの手番です。CLIの応答を待っています。", "status.scoring": "整地を確認中です。石を印すか点数を承認します。", "status.finished": "終了 · {result}", "status.draw": "引き分け · {result}", "lastMove.heading": "直前の着手", "lastMove.empty": "まだ着手はありません", "lastMove.waiting": "最初の着手を待っています", "history.heading": "着手履歴", "history.count": "{count}手", "history.empty": "対局を始めると着手がここに表示されます。", "score.heading": "点数", "score.black": "黒", "score.white": "白", "score.territoryBlack": "黒地", "score.territoryWhite": "白地", "score.komi": "コミ", "score.prisoners": "アゲハマ", "score.waiting": "両者がパスすると点数の詳細を表示します。", "score.dead": "死に石", "score.seki": "セキ", "score.accept": "点数を承認", "score.resume": "対局を再開", "score.review": "確認", "score.final": "最終", "score.live": "進行中", "score.modeLabel": "石を印す", "setup.eyebrow": "新しい対局 · 盤の設定", "setup.heading": "新しい対局を設定", "setup.description": "石の色と盤の大きさを選びます。LLMは別のCLIから着手します。", "setup.colorLabel": "あなたの石", "setup.groupAria": "人間の石の色選択", "setup.sizeLabel": "盤の大きさ", "setup.sizeAria": "盤の大きさの選択", "setup.black.label": "黒を持つ", "setup.black.detail": "あなたが先手", "setup.white.label": "白を持つ", "setup.white.detail": "LLMが先手", "setup.size.default": "標準", "setup.size.medium": "中盤", "setup.size.small": "早碁", "setup.start": "対局を始める", "point.stone": "{point}、{color}石", "point.empty": "{point}、空の交点", "point.legal": "合法な着手", "color.black": "黒", "color.white": "白", "actor.human": "人間", "actor.llm": "LLM", "takeback.request.heading": "待ったを求めますか？", "takeback.request.cancel": "キャンセル", "takeback.request.confirm": "求める", "takeback.response.heading": "LLMが待ったを求めています", "takeback.response.reject": "拒否", "takeback.response.accept": "承認", "resign.heading": "投了しますか？", "resign.confirm": "投了", "confirm.newGame": "現在の対局を破棄して新しい対局を始めますか？", "error.generic": "予期しないサーバーエラーです。もう一度お試しください。", "error.connect": "サーバーに接続できません。", "error.state": "サーバー状態を読み取れません。", "error.move": "着手を送信できません。", "error.start": "新しい対局を始められません。", "error.score": "点数を更新できません。", "error.takeback": "待ったの操作を送信できません。", "error.resign": "投了できません。", "error.noGame": "対局がありません。先に対局を始めてください。", "error.gameOver": "対局はすでに終了しています。", "error.wrongTurn": "あなたの手番ではありません。", "error.illegalMove": "その着手はできません：{move}", "error.invalidColor": "黒か白を選んでください。", "error.invalidBoardSize": "9×9、13×13、19×19から選んでください。", "error.takebackUnavailable": "今は待ったを使えません。", "error.takebackPending": "返答待ちの待ったがあります。", "error.noPendingTakeback": "返答する待ったがありません。", "error.resignUnavailable": "今は投了できません。", "error.scoreNotScoring": "点数操作は整地確認中だけ使えます。", "error.pointRequired": "印を付ける石のグループを選んでください。", "error.invalidPoint": "この交点は操作に使えません。", "error.staleRevision": "点数が変わりました。盤面を確認して再試行してください。", "error.alreadyAccepted": "点数は承認済みです。相手を待っています。", "error.invalidAction": "今はその操作を使えません。", "error.gameExists": "すでに対局中です。" },
  es: { "meta.title": "LLM Baduk · Mesa local de go", "brand.tagline": "PARTIDA LOCAL · HUMANO × LLM", "match.none": "Sin partida", "match.game": "Partida {id}", "toolbar.newGame": "Nueva partida", "toolbar.takeback": "Deshacer", "toolbar.resign": "Abandonar", "language.label": "Idioma", "workspace.aria": "Mesa de go", "board.section": "TABLERO", "board.currentGame": "Partida actual", "board.chooseColor": "Elige color y tamaño para iniciar una partida", "board.caption.human": "{color} · Turno humano · {size}×{size}", "board.caption.llm": "{color} · Turno del LLM · {size}×{size}", "board.caption.scoring": "Revisión de puntuación · {size}×{size}", "board.caption.terminal": "{color} · Partida terminada · {size}×{size}", "board.aria": "Tablero de go", "board.controls": "Controles del tablero", "board.pass": "Pasar", "turn.heading": "TURNO ACTIVO", "clock.setup.label": "PARTIDA LISTA", "clock.setup.detail": "Elige color y tamaño para comenzar.", "clock.human.label": "TURNO HUMANO", "clock.human.value": "TU TURNO", "clock.human.detail": "Coloca una piedra {color} o pasa.", "clock.llm.label": "TURNO DEL LLM", "clock.llm.value": "TURNO DEL LLM", "clock.llm.detail": "Esperando la jugada {color} del CLI.", "clock.scoring.label": "REVISIÓN", "clock.scoring.value": "MARCAR", "clock.scoring.detail": "Marca grupos muertos o seki y acepta la puntuación mostrada.", "clock.finished.label": "FINALIZADA", "clock.draw.label": "TABLAS", "clock.terminal.value": "FIN", "status.setup": "Elige color y tamaño para iniciar una partida.", "status.human": "Tu turno. Elige una intersección libre.", "status.llm": "Turno del LLM. Esperando la respuesta del CLI.", "status.scoring": "Revisión de puntuación. Marca grupos o acepta la puntuación.", "status.finished": "Finalizada · {result}", "status.draw": "Tablas · {result}", "lastMove.heading": "ÚLTIMA JUGADA", "lastMove.empty": "Aún no hay jugadas", "lastMove.waiting": "Esperando la primera jugada", "history.heading": "HISTORIAL", "history.count": "{count} jugadas", "history.empty": "Las jugadas aparecerán aquí al comenzar.", "score.heading": "PUNTUACIÓN", "score.black": "Negro", "score.white": "Blanco", "score.territoryBlack": "Territorio N", "score.territoryWhite": "Territorio B", "score.komi": "Komi", "score.prisoners": "Prisioneras", "score.waiting": "Los detalles aparecen después de dos pases.", "score.dead": "Piedras muertas", "score.seki": "Grupos seki", "score.accept": "Aceptar puntuación", "score.resume": "Reanudar", "score.review": "REVISIÓN", "score.final": "FINAL", "score.live": "EN JUEGO", "score.modeLabel": "MARCAR GRUPOS", "setup.eyebrow": "NUEVA PARTIDA · CONFIGURA EL TABLERO", "setup.heading": "Configura una partida", "setup.description": "Elige tus piedras y el tamaño. El LLM juega desde un CLI separado.", "setup.colorLabel": "Tus piedras", "setup.groupAria": "Selección de color humano", "setup.sizeLabel": "Tamaño", "setup.sizeAria": "Selección del tamaño", "setup.black.label": "Jugar con negras", "setup.black.detail": "Juegas primero", "setup.white.label": "Jugar con blancas", "setup.white.detail": "El LLM juega primero", "setup.size.default": "Estándar", "setup.size.medium": "Mediano", "setup.size.small": "Partida rápida", "setup.start": "Iniciar partida", "point.stone": "{point}, piedra {color}", "point.empty": "{point}, intersección vacía", "point.legal": "jugada legal", "color.black": "Negro", "color.white": "Blanco", "actor.human": "Humano", "actor.llm": "LLM", "takeback.request.heading": "¿Solicitar deshacer?", "takeback.request.cancel": "Cancelar", "takeback.request.confirm": "Solicitar", "takeback.response.heading": "El LLM solicita deshacer", "takeback.response.reject": "Rechazar", "takeback.response.accept": "Aceptar", "resign.heading": "¿Abandonar la partida?", "resign.confirm": "Abandonar", "confirm.newGame": "¿Descartar la partida actual y comenzar otra?", "error.generic": "El servidor devolvió un error inesperado. Inténtalo de nuevo.", "error.connect": "No se pudo conectar al servidor.", "error.state": "No se pudo leer el estado del servidor.", "error.move": "No se pudo enviar la jugada.", "error.start": "No se pudo iniciar la partida.", "error.score": "No se pudo actualizar la puntuación.", "error.takeback": "No se pudo enviar la acción de deshacer.", "error.resign": "No se pudo abandonar la partida.", "error.noGame": "No hay una partida activa. Inicia una primero.", "error.gameOver": "La partida ya terminó.", "error.wrongTurn": "No es tu turno.", "error.illegalMove": "La jugada no es legal: {move}", "error.invalidColor": "Elige negras o blancas.", "error.invalidBoardSize": "Elige un tablero de 9×9, 13×13 o 19×19.", "error.takebackUnavailable": "No se puede deshacer ahora.", "error.takebackPending": "Ya hay una solicitud de deshacer pendiente.", "error.noPendingTakeback": "No hay una solicitud que responder.", "error.resignUnavailable": "No se puede abandonar ahora.", "error.scoreNotScoring": "Las acciones de puntuación solo están disponibles al revisar.", "error.pointRequired": "Elige un grupo para marcar.", "error.invalidPoint": "Esa intersección no está disponible.", "error.staleRevision": "La puntuación cambió. Revisa el tablero y vuelve a intentarlo.", "error.alreadyAccepted": "Ya aceptaste la puntuación. Espera al otro lado.", "error.invalidAction": "Esta acción no está disponible ahora.", "error.gameExists": "Ya hay una partida en curso." },
  fr: { "meta.title": "LLM Baduk · Atelier de go local", "brand.tagline": "PARTIE LOCALE · HUMAIN × LLM", "match.none": "Aucune partie", "match.game": "Partie {id}", "toolbar.newGame": "Nouvelle partie", "toolbar.takeback": "Annuler le coup", "toolbar.resign": "Abandonner", "language.label": "Langue", "workspace.aria": "Atelier de go", "board.section": "PLATEAU", "board.currentGame": "Partie actuelle", "board.chooseColor": "Choisissez la couleur et la taille pour commencer", "board.caption.human": "{color} · Tour humain · {size}×{size}", "board.caption.llm": "{color} · Tour du LLM · {size}×{size}", "board.caption.scoring": "Vérification du score · {size}×{size}", "board.caption.terminal": "{color} · Partie terminée · {size}×{size}", "board.aria": "Plateau de go", "board.controls": "Commandes du plateau", "board.pass": "Passer", "turn.heading": "TOUR ACTIF", "clock.setup.label": "PARTIE PRÊTE", "clock.setup.detail": "Choisissez une couleur et une taille.", "clock.human.label": "TOUR HUMAIN", "clock.human.value": "À VOUS", "clock.human.detail": "Posez une pierre {color} ou passez.", "clock.llm.label": "TOUR DU LLM", "clock.llm.value": "TOUR DU LLM", "clock.llm.detail": "En attente du coup {color} depuis le CLI.", "clock.scoring.label": "VÉRIFICATION", "clock.scoring.value": "MARQUER", "clock.scoring.detail": "Marquez les groupes morts ou seki puis acceptez le score affiché.", "clock.finished.label": "TERMINÉE", "clock.draw.label": "NULLE", "clock.terminal.value": "FIN", "status.setup": "Choisissez une couleur et une taille pour commencer.", "status.human": "À vous. Choisissez une intersection libre.", "status.llm": "Tour du LLM. En attente de la réponse du CLI.", "status.scoring": "Vérification du score. Marquez les groupes ou acceptez le score.", "status.finished": "Terminée · {result}", "status.draw": "Nulle · {result}", "lastMove.heading": "DERNIER COUP", "lastMove.empty": "Aucun coup", "lastMove.waiting": "En attente du premier coup", "history.heading": "HISTORIQUE", "history.count": "{count} coups", "history.empty": "Les coups apparaîtront ici après le début.", "score.heading": "SCORE", "score.black": "Noir", "score.white": "Blanc", "score.territoryBlack": "Territoire N", "score.territoryWhite": "Territoire B", "score.komi": "Komi", "score.prisoners": "Prisonniers", "score.waiting": "Les détails apparaissent après deux passes.", "score.dead": "Pierres mortes", "score.seki": "Groupes seki", "score.accept": "Accepter le score", "score.resume": "Reprendre", "score.review": "VÉRIFICATION", "score.final": "FINAL", "score.live": "EN COURS", "score.modeLabel": "MARQUER LES GROUPES", "setup.eyebrow": "NOUVELLE PARTIE · CONFIGURER LE PLATEAU", "setup.heading": "Configurer une partie", "setup.description": "Choisissez vos pierres et la taille. Le LLM joue depuis un CLI séparé.", "setup.colorLabel": "Vos pierres", "setup.groupAria": "Sélection de la couleur humaine", "setup.sizeLabel": "Taille du plateau", "setup.sizeAria": "Sélection de la taille", "setup.black.label": "Jouer les noirs", "setup.black.detail": "Vous commencez", "setup.white.label": "Jouer les blancs", "setup.white.detail": "Le LLM commence", "setup.size.default": "Standard", "setup.size.medium": "Moyen", "setup.size.small": "Partie rapide", "setup.start": "Commencer", "point.stone": "{point}, pierre {color}", "point.empty": "{point}, intersection vide", "point.legal": "coup légal", "color.black": "Noir", "color.white": "Blanc", "actor.human": "Humain", "actor.llm": "LLM", "takeback.request.heading": "Demander l'annulation ?", "takeback.request.cancel": "Annuler", "takeback.request.confirm": "Demander", "takeback.response.heading": "Le LLM demande une annulation", "takeback.response.reject": "Refuser", "takeback.response.accept": "Accepter", "resign.heading": "Abandonner la partie ?", "resign.confirm": "Abandonner", "confirm.newGame": "Abandonner la partie actuelle et en commencer une nouvelle ?", "error.generic": "Le serveur a renvoyé une erreur inattendue. Réessayez.", "error.connect": "Connexion au serveur impossible.", "error.state": "Lecture de l'état du serveur impossible.", "error.move": "Envoi du coup impossible.", "error.start": "Démarrage impossible.", "error.score": "Mise à jour du score impossible.", "error.takeback": "Envoi de l'action impossible.", "error.resign": "Abandon impossible.", "error.noGame": "Aucune partie en cours. Commencez-en une.", "error.gameOver": "La partie est déjà terminée.", "error.wrongTurn": "Ce n'est pas votre tour.", "error.illegalMove": "Ce coup est illégal : {move}", "error.invalidColor": "Choisissez noir ou blanc.", "error.invalidBoardSize": "Choisissez un plateau 9×9, 13×13 ou 19×19.", "error.takebackUnavailable": "Annulation indisponible pour le moment.", "error.takebackPending": "Une demande d'annulation attend déjà une réponse.", "error.noPendingTakeback": "Aucune demande à traiter.", "error.resignUnavailable": "Abandon indisponible pour le moment.", "error.scoreNotScoring": "Les actions de score ne sont disponibles qu'en vérification.", "error.pointRequired": "Choisissez un groupe à marquer.", "error.invalidPoint": "Cette intersection n'est pas disponible.", "error.staleRevision": "Le score a changé. Vérifiez le plateau et réessayez.", "error.alreadyAccepted": "Score déjà accepté. Attendez l'autre joueur.", "error.invalidAction": "Cette action n'est pas disponible maintenant.", "error.gameExists": "Une partie est déjà en cours." },
  de: { "meta.title": "LLM Baduk · Lokale Go-Werkbank", "brand.tagline": "LOKALE PARTIE · MENSCH × LLM", "match.none": "Keine Partie", "match.game": "Partie {id}", "toolbar.newGame": "Neue Partie", "toolbar.takeback": "Rücknahme", "toolbar.resign": "Aufgeben", "language.label": "Sprache", "workspace.aria": "Go-Werkbank", "board.section": "BRETT", "board.currentGame": "Aktuelle Partie", "board.chooseColor": "Farbe und Brettgröße für eine neue Partie wählen", "board.caption.human": "{color} · Mensch am Zug · {size}×{size}", "board.caption.llm": "{color} · LLM am Zug · {size}×{size}", "board.caption.scoring": "Punkteprüfung · {size}×{size}", "board.caption.terminal": "{color} · Partie beendet · {size}×{size}", "board.aria": "Go-Brett", "board.controls": "Brettsteuerung", "board.pass": "Passen", "turn.heading": "AKTIVER ZUG", "clock.setup.label": "PARTIE BEREIT", "clock.setup.detail": "Farbe und Größe zum Start wählen.", "clock.human.label": "MENSCH AM ZUG", "clock.human.value": "DU BIST DRAN", "clock.human.detail": "{color} Stein setzen oder passen.", "clock.llm.label": "LLM AM ZUG", "clock.llm.value": "LLM AM ZUG", "clock.llm.detail": "Warte auf den {color} Zug aus dem CLI.", "clock.scoring.label": "PUNKTEPRÜFUNG", "clock.scoring.value": "MARKIEREN", "clock.scoring.detail": "Tote oder Seki-Gruppen markieren und die angezeigte Wertung annehmen.", "clock.finished.label": "BEENDET", "clock.draw.label": "UNENTSCHIEDEN", "clock.terminal.value": "ENDE", "status.setup": "Farbe und Größe für eine neue Partie wählen.", "status.human": "Du bist dran. Wähle eine freie Kreuzung.", "status.llm": "Der LLM ist am Zug. Warte auf die CLI-Antwort.", "status.scoring": "Punkteprüfung. Gruppen markieren oder angezeigte Wertung annehmen.", "status.finished": "Beendet · {result}", "status.draw": "Unentschieden · {result}", "lastMove.heading": "LETZTER ZUG", "lastMove.empty": "Noch keine Züge", "lastMove.waiting": "Warte auf den ersten Zug", "history.heading": "ZUGFOLGE", "history.count": "{count} Züge", "history.empty": "Die Züge erscheinen hier nach dem Start.", "score.heading": "WERTUNG", "score.black": "Schwarz", "score.white": "Weiß", "score.territoryBlack": "Gebiet S", "score.territoryWhite": "Gebiet W", "score.komi": "Komi", "score.prisoners": "Gefangene", "score.waiting": "Details erscheinen nach zwei Pässen.", "score.dead": "Tote Steine", "score.seki": "Seki-Gruppen", "score.accept": "Wertung annehmen", "score.resume": "Weiterspielen", "score.review": "PRÜFUNG", "score.final": "FINAL", "score.live": "LAUFEND", "score.modeLabel": "GRUPPEN MARKIEREN", "setup.eyebrow": "NEUE PARTIE · BRETT EINRICHTEN", "setup.heading": "Neue Partie einrichten", "setup.description": "Steine und Brettgröße wählen. Der LLM spielt über ein separates CLI.", "setup.colorLabel": "Deine Steine", "setup.groupAria": "Auswahl der Menschenfarbe", "setup.sizeLabel": "Brettgröße", "setup.sizeAria": "Auswahl der Brettgröße", "setup.black.label": "Schwarz spielen", "setup.black.detail": "Du beginnst", "setup.white.label": "Weiß spielen", "setup.white.detail": "Der LLM beginnt", "setup.size.default": "Standard", "setup.size.medium": "Mittel", "setup.size.small": "Schnelle Partie", "setup.start": "Partie starten", "point.stone": "{point}, {color} Stein", "point.empty": "{point}, freie Kreuzung", "point.legal": "legaler Zug", "color.black": "Schwarz", "color.white": "Weiß", "actor.human": "Mensch", "actor.llm": "LLM", "takeback.request.heading": "Rücknahme anfragen?", "takeback.request.cancel": "Abbrechen", "takeback.request.confirm": "Anfragen", "takeback.response.heading": "Der LLM bittet um Rücknahme", "takeback.response.reject": "Ablehnen", "takeback.response.accept": "Annehmen", "resign.heading": "Partie aufgeben?", "resign.confirm": "Aufgeben", "confirm.newGame": "Aktuelle Partie verwerfen und neue starten?", "error.generic": "Der Server meldete einen unerwarteten Fehler. Erneut versuchen.", "error.connect": "Verbindung zum Server nicht möglich.", "error.state": "Serverstatus kann nicht gelesen werden.", "error.move": "Zug kann nicht gesendet werden.", "error.start": "Neue Partie kann nicht gestartet werden.", "error.score": "Wertung kann nicht aktualisiert werden.", "error.takeback": "Rücknahmeaktion kann nicht gesendet werden.", "error.resign": "Aufgeben nicht möglich.", "error.noGame": "Keine Partie läuft. Zuerst eine Partie starten.", "error.gameOver": "Die Partie ist bereits beendet.", "error.wrongTurn": "Du bist nicht am Zug.", "error.illegalMove": "Dieser Zug ist nicht legal: {move}", "error.invalidColor": "Schwarz oder Weiß wählen.", "error.invalidBoardSize": "9×9, 13×13 oder 19×19 wählen.", "error.takebackUnavailable": "Jetzt ist keine Rücknahme möglich.", "error.takebackPending": "Eine Rücknahmeanfrage wartet bereits auf Antwort.", "error.noPendingTakeback": "Keine Rücknahmeanfrage zu beantworten.", "error.resignUnavailable": "Jetzt kann nicht aufgegeben werden.", "error.scoreNotScoring": "Wertungsaktionen sind nur bei der Punkteprüfung verfügbar.", "error.pointRequired": "Eine zu markierende Gruppe wählen.", "error.invalidPoint": "Diese Kreuzung ist für diese Aktion nicht verfügbar.", "error.staleRevision": "Die Wertung hat sich geändert. Brett prüfen und erneut versuchen.", "error.alreadyAccepted": "Wertung bereits angenommen. Auf die andere Seite warten.", "error.invalidAction": "Diese Aktion ist jetzt nicht verfügbar.", "error.gameExists": "Eine Partie läuft bereits." },
};

const COMMON_LOCALE_OVERRIDES = {
  "zh-Hans": {
    "toolbar.actions": "游戏操作", "board.waiting": "等待服务器状态", "status.connecting": "正在连接服务器。", "status.connectionError": "服务器请求错误 · 请查看下方信息。", "status.disconnected": "服务器连接已断开 · 正在自动重连。", "status.requestError": "请求错误 · 查看下方信息后重试。", "status.resigned": "{actor} 已认输 · 对局结束。", "board.revisionInitial": "版本 0", "board.revision": "版本 {revision}", "connection.aria": "连接状态", "connection.label": "连接", "connection.connecting": "检查中", "connection.connected": "已连接", "connection.disconnected": "重连中", "connection.error": "请求错误", "history.aria": "当前对局着手记录", "takeback.aria": "悔棋操作对话框", "takeback.dialog.eyebrow": "游戏操作 · 悔棋", "takeback.request.description": "请求 LLM 悔棋 {plies} 手，包括第 {target} 手。", "clock.error.label": "请求错误", "clock.error.value": "检查", "clock.error.detail": "查看连接状态和错误信息。", "clock.disconnected.label": "重连中", "clock.disconnected.value": "等待", "clock.disconnected.detail": "事件流将自动重连。", "clock.requestError.label": "请求错误", "clock.requestError.value": "重试", "clock.requestError.detail": "查看错误信息后重新选择操作。", "clock.resigned.label": "认输", "clock.resigned.value": "结束", "clock.resigned.detail": "{actor} 已认输。对局结束。", "clock.takeback.label": "悔棋", "clock.finished.detail": "双方都已接受计分。", "live.connected": " 已连接", "live.waiting": " 等待", "score.accepted": "人类 {human} · LLM {llm}", "score.acceptedShort": "已接受", "score.pendingShort": "等待", "score.breakdown": "棋地：黑 {black} · 白 {white}", "lastMove.meta": "{actor} · {color} · 提子 {captured}", "history.itemAria": "第 {ply} 手：{move}，{color}，{actor}", "resign.dialog.eyebrow": "游戏操作 · 认输", "resign.description": "认输后对局结束，另一方获胜。", "resign.aria": "认输确认对话框", "takeback.response.description": "此次请求悔棋 {plies} 手，包括第 {target} 手。"
  },
  "zh-Hant": {
    "toolbar.actions": "遊戲操作", "board.waiting": "等待伺服器狀態", "status.connecting": "正在連線伺服器。", "status.connectionError": "伺服器請求錯誤 · 請查看下方資訊。", "status.disconnected": "伺服器連線已中斷 · 正在自動重連。", "status.requestError": "請求錯誤 · 查看下方資訊後重試。", "status.resigned": "{actor} 已認輸 · 對局結束。", "board.revisionInitial": "版本 0", "board.revision": "版本 {revision}", "connection.aria": "連線狀態", "connection.label": "連線", "connection.connecting": "檢查中", "connection.connected": "已連線", "connection.disconnected": "重連中", "connection.error": "請求錯誤", "history.aria": "目前對局著手記錄", "takeback.aria": "悔棋操作對話框", "takeback.dialog.eyebrow": "遊戲操作 · 悔棋", "takeback.request.description": "請求 LLM 悔棋 {plies} 手，包括第 {target} 手。", "clock.error.label": "請求錯誤", "clock.error.value": "檢查", "clock.error.detail": "查看連線狀態和錯誤資訊。", "clock.disconnected.label": "重連中", "clock.disconnected.value": "等待", "clock.disconnected.detail": "事件流將自動重連。", "clock.requestError.label": "請求錯誤", "clock.requestError.value": "重試", "clock.requestError.detail": "查看錯誤資訊後重新選擇操作。", "clock.resigned.label": "認輸", "clock.resigned.value": "結束", "clock.resigned.detail": "{actor} 已認輸。對局結束。", "clock.takeback.label": "悔棋", "clock.finished.detail": "雙方都已接受計分。", "live.connected": " 已連線", "live.waiting": " 等待", "score.accepted": "人類 {human} · LLM {llm}", "score.acceptedShort": "已接受", "score.pendingShort": "等待", "score.breakdown": "棋地：黑 {black} · 白 {white}", "lastMove.meta": "{actor} · {color} · 提子 {captured}", "history.itemAria": "第 {ply} 手：{move}，{color}，{actor}", "resign.dialog.eyebrow": "遊戲操作 · 認輸", "resign.description": "認輸後對局結束，另一方獲勝。", "resign.aria": "認輸確認對話框", "takeback.response.description": "此次請求悔棋 {plies} 手，包括第 {target} 手。"
  },
  ja: {
    "toolbar.actions": "対局操作", "board.waiting": "サーバー状態を待っています", "status.connecting": "サーバーに接続しています。", "status.connectionError": "サーバーリクエストエラー · 下のメッセージを確認してください。", "status.disconnected": "サーバー接続が切れました · 自動で再接続します。", "status.requestError": "リクエストエラー · 下のメッセージを確認して再試行してください。", "status.resigned": "{actor}が投了 · 対局終了。", "board.revisionInitial": "REV 0", "board.revision": "REV {revision}", "connection.aria": "接続状態", "connection.label": "接続", "connection.connecting": "確認中", "connection.connected": "接続済み", "connection.disconnected": "再接続中", "connection.error": "リクエストエラー", "history.aria": "現在の対局の着手履歴", "takeback.aria": "待った操作ダイアログ", "takeback.dialog.eyebrow": "対局操作 · 待った", "takeback.request.description": "LLMに{plies}手（第{target}手を含む）の待ったを求めます。", "clock.error.label": "リクエストエラー", "clock.error.value": "確認", "clock.error.detail": "接続状態とエラーメッセージを確認してください。", "clock.disconnected.label": "再接続中", "clock.disconnected.value": "待機", "clock.disconnected.detail": "イベントストリームは自動で再接続します。", "clock.requestError.label": "リクエストエラー", "clock.requestError.value": "再試行", "clock.requestError.detail": "エラーを確認してから操作を選び直してください。", "clock.resigned.label": "投了", "clock.resigned.value": "終了", "clock.resigned.detail": "{actor}が投了しました。対局終了です。", "clock.takeback.label": "待った", "clock.finished.detail": "両者が点数を承認しました。", "live.connected": " 接続済み", "live.waiting": " 待機", "score.accepted": "人間 {human} · LLM {llm}", "score.acceptedShort": "承認済み", "score.pendingShort": "待機中", "score.breakdown": "地：黒 {black} · 白 {white}", "lastMove.meta": "{actor} · {color} · 取った石 {captured}", "history.itemAria": "{ply}手目：{move}、{color}、{actor}", "resign.dialog.eyebrow": "対局操作 · 投了", "resign.description": "投了すると対局が終了し、相手の勝ちになります。", "resign.aria": "投了確認ダイアログ", "takeback.response.description": "第{target}手を含む{plies}手を戻します。"
  },
  es: {
    "toolbar.actions": "Acciones", "board.waiting": "Esperando el estado del servidor", "status.connecting": "Conectando con el servidor.", "status.connectionError": "Error de solicitud · Revisa el mensaje inferior.", "status.disconnected": "Se perdió la conexión · Reconectando automáticamente.", "status.requestError": "Error de solicitud · Revisa el mensaje y vuelve a intentarlo.", "status.resigned": "{actor} abandonó · Partida terminada.", "board.revisionInitial": "REV 0", "board.revision": "REV {revision}", "connection.aria": "Estado de conexión", "connection.label": "Conexión", "connection.connecting": "Comprobando", "connection.connected": "Conectado", "connection.disconnected": "Reconectando", "connection.error": "Error de solicitud", "history.aria": "Historial de jugadas actual", "takeback.aria": "Diálogo de deshacer", "takeback.dialog.eyebrow": "ACCIÓN · DESHACER", "takeback.request.description": "Pide al LLM deshacer {plies} jugada(s), incluida la jugada {target}.", "clock.error.label": "ERROR", "clock.error.value": "REVISAR", "clock.error.detail": "Revisa la conexión y el mensaje de error.", "clock.disconnected.label": "RECONECTANDO", "clock.disconnected.value": "ESPERA", "clock.disconnected.detail": "El flujo de eventos se reconectará automáticamente.", "clock.requestError.label": "ERROR", "clock.requestError.value": "REINTENTAR", "clock.requestError.detail": "Revisa el error y elige de nuevo una acción.", "clock.resigned.label": "ABANDONO", "clock.resigned.value": "FIN", "clock.resigned.detail": "{actor} abandonó. La partida terminó.", "clock.takeback.label": "DESHACER", "clock.finished.detail": "Ambos lados aceptaron la puntuación.", "live.connected": " CONECTADO", "live.waiting": " ESPERA", "score.accepted": "Humano {human} · LLM {llm}", "score.acceptedShort": "aceptada", "score.pendingShort": "esperando", "score.breakdown": "Territorio: N {black} · B {white}", "lastMove.meta": "{actor} · {color} · capturadas {captured}", "history.itemAria": "Jugada {ply}: {move}, {color}, {actor}", "resign.dialog.eyebrow": "ACCIÓN · ABANDONAR", "resign.description": "Abandonar termina la partida y da la victoria al otro lado.", "resign.aria": "Diálogo de confirmación de abandono", "takeback.response.description": "La solicitud deshace {plies} jugada(s), incluida la jugada {target}."
  },
  fr: {
    "toolbar.actions": "Actions", "board.waiting": "En attente de l'état du serveur", "status.connecting": "Connexion au serveur.", "status.connectionError": "Erreur de requête · Vérifiez le message ci-dessous.", "status.disconnected": "Connexion perdue · Reconnexion automatique.", "status.requestError": "Erreur de requête · Vérifiez le message et réessayez.", "status.resigned": "{actor} a abandonné · Partie terminée.", "board.revisionInitial": "REV 0", "board.revision": "REV {revision}", "connection.aria": "État de la connexion", "connection.label": "Connexion", "connection.connecting": "Vérification", "connection.connected": "Connecté", "connection.disconnected": "Reconnexion", "connection.error": "Erreur de requête", "history.aria": "Historique de la partie actuelle", "takeback.aria": "Dialogue d'annulation", "takeback.dialog.eyebrow": "ACTION · ANNULATION", "takeback.request.description": "Demander au LLM d'annuler {plies} coup(s), dont le coup {target}.", "clock.error.label": "ERREUR", "clock.error.value": "VÉRIFIER", "clock.error.detail": "Vérifiez la connexion et le message d'erreur.", "clock.disconnected.label": "RECONNEXION", "clock.disconnected.value": "ATTENTE", "clock.disconnected.detail": "Le flux d'événements se reconnectera automatiquement.", "clock.requestError.label": "ERREUR", "clock.requestError.value": "RÉESSAYER", "clock.requestError.detail": "Vérifiez l'erreur puis choisissez une action.", "clock.resigned.label": "ABANDON", "clock.resigned.value": "FIN", "clock.resigned.detail": "{actor} a abandonné. La partie est terminée.", "clock.takeback.label": "ANNULATION", "clock.finished.detail": "Les deux camps ont accepté le score.", "live.connected": " CONNECTÉ", "live.waiting": " ATTENTE", "score.accepted": "Humain {human} · LLM {llm}", "score.acceptedShort": "accepté", "score.pendingShort": "en attente", "score.breakdown": "Territoire : N {black} · B {white}", "lastMove.meta": "{actor} · {color} · capturées {captured}", "history.itemAria": "Coup {ply} : {move}, {color}, {actor}", "resign.dialog.eyebrow": "ACTION · ABANDON", "resign.description": "Abandonner termine la partie et donne la victoire à l'autre camp.", "resign.aria": "Dialogue de confirmation d'abandon", "takeback.response.description": "La demande annule {plies} coup(s), dont le coup {target}."
  },
  de: {
    "toolbar.actions": "Partieaktionen", "board.waiting": "Warte auf Serverstatus", "status.connecting": "Verbindung zum Server wird hergestellt.", "status.connectionError": "Serveranfragefehler · Nachricht unten prüfen.", "status.disconnected": "Serververbindung verloren · Automatische Wiederverbindung.", "status.requestError": "Anfragefehler · Nachricht prüfen und erneut versuchen.", "status.resigned": "{actor} hat aufgegeben · Partie beendet.", "board.revisionInitial": "REV 0", "board.revision": "REV {revision}", "connection.aria": "Verbindungsstatus", "connection.label": "Verbindung", "connection.connecting": "Prüfung", "connection.connected": "Verbunden", "connection.disconnected": "Wiederverbindung", "connection.error": "Anfragefehler", "history.aria": "Zugfolge der aktuellen Partie", "takeback.aria": "Dialog zur Rücknahme", "takeback.dialog.eyebrow": "PARTIEAKTION · RÜCKNAHME", "takeback.request.description": "Den LLM bitten, {plies} Zug(e) einschließlich Zug {target} zurückzunehmen.", "clock.error.label": "ANFRAGEFEHLER", "clock.error.value": "PRÜFEN", "clock.error.detail": "Verbindung und Fehlermeldung prüfen.", "clock.disconnected.label": "WIEDERVERBINDUNG", "clock.disconnected.value": "WARTEN", "clock.disconnected.detail": "Der Ereignisstrom verbindet sich automatisch neu.", "clock.requestError.label": "ANFRAGEFEHLER", "clock.requestError.value": "ERNEUT", "clock.requestError.detail": "Fehler prüfen und Aktion erneut wählen.", "clock.resigned.label": "AUFGABE", "clock.resigned.value": "ENDE", "clock.resigned.detail": "{actor} hat aufgegeben. Die Partie ist beendet.", "clock.takeback.label": "RÜCKNAHME", "clock.finished.detail": "Beide Seiten haben die Wertung angenommen.", "live.connected": " VERBUNDEN", "live.waiting": " WARTEN", "score.accepted": "Mensch {human} · LLM {llm}", "score.acceptedShort": "angenommen", "score.pendingShort": "wartend", "score.breakdown": "Gebiet: S {black} · W {white}", "lastMove.meta": "{actor} · {color} · gefangen {captured}", "history.itemAria": "Zug {ply}: {move}, {color}, {actor}", "resign.dialog.eyebrow": "PARTIEAKTION · AUFGEBEN", "resign.description": "Aufgeben beendet die Partie und gibt dem anderen die Wertung.", "resign.aria": "Bestätigungsdialog zum Aufgeben", "takeback.response.description": "Die Anfrage nimmt {plies} Zug(e) einschließlich Zug {target} zurück."
  },
};
const KOREAN_LOCALE_OVERRIDES = {
  "meta.title": "LLM Baduk · 로컬 바둑 워크벤치", "meta.description": "브라우저의 사람과 CLI LLM이 한 대국을 함께 진행하는 로컬 바둑 워크벤치입니다.", "brand.tagline": "로컬 대국 · 사람 × LLM", "match.none": "대국 없음", "match.game": "대국 {id}", "toolbar.newGame": "새 대국", "toolbar.actions": "게임 동작", "toolbar.takeback": "무르기", "toolbar.resign": "기권", "language.label": "언어", "workspace.aria": "바둑 작업대", "board.section": "바둑판", "board.currentGame": "현재 대국", "board.waiting": "서버 상태 대기 중", "board.chooseColor": "새 대국의 색과 판 크기를 고르세요", "board.caption.human": "{color} · 사람 차례 · {size}×{size}", "board.caption.llm": "{color} · LLM 차례 · {size}×{size}", "board.caption.scoring": "계가 검토 · {size}×{size}", "board.caption.terminal": "{color} · 대국 종료 · {size}×{size}", "board.aria": "바둑판", "board.controls": "바둑판 조작", "board.pass": "패스", "board.revisionInitial": "리비전 0", "board.revision": "리비전 {revision}", "turn.heading": "현재 차례", "live.connected": " 연결됨", "live.waiting": " 대기", "clock.setup.label": "대국 준비", "clock.setup.value": "—", "clock.setup.detail": "시작할 색과 판 크기를 고르세요.", "clock.error.label": "요청 오류", "clock.error.value": "확인", "clock.error.detail": "연결 상태와 오류 문구를 확인하세요.", "clock.disconnected.label": "재연결 중", "clock.disconnected.value": "대기", "clock.disconnected.detail": "이벤트 스트림이 자동으로 다시 연결됩니다.", "clock.requestError.label": "요청 오류", "clock.requestError.value": "재시도", "clock.requestError.detail": "오류를 확인한 뒤 다시 행동을 고르세요.", "clock.scoring.label": "계가 검토", "clock.scoring.value": "표시", "clock.scoring.detail": "사석이나 빅인 돌 무리를 표시한 뒤 현재 점수를 수락하세요.", "clock.finished.label": "종료", "clock.finished.detail": "양쪽이 점수를 수락했습니다.", "clock.draw.label": "무승부", "clock.terminal.value": "종료", "clock.human.label": "사람 차례", "clock.human.value": "당신의 차례", "clock.human.detail": "{color} 돌을 놓거나 패스하세요.", "clock.llm.label": "LLM 차례", "clock.llm.value": "LLM 차례", "clock.llm.detail": "CLI에서 {color} 수를 보내기를 기다립니다.", "clock.takeback.label": "무르기", "clock.takeback.outgoingValue": "대기", "clock.takeback.incomingValue": "응답", "clock.takeback.outgoingDetail": "LLM의 무르기 응답을 기다립니다.", "clock.takeback.incomingDetail": "LLM이 최근 수를 무르려 합니다. 응답을 고르세요.", "clock.resigned.label": "기권", "clock.resigned.value": "종료", "clock.resigned.detail": "{actor}이(가) 기권했습니다. 대국이 끝났습니다.", "status.connectionError": "서버 요청 오류 · 아래 문구를 확인하세요.", "status.connecting": "서버에 연결하는 중입니다.", "status.disconnected": "서버 연결이 끊겼습니다 · 자동으로 재연결합니다.", "status.requestError": "요청 오류 · 아래 문구를 확인하고 다시 시도하세요.", "status.setup": "색과 판 크기를 골라 새 대국을 시작하세요.", "status.human": "당신의 차례입니다. 빈 교차점을 고르세요.", "status.llm": "LLM 차례입니다. CLI 응답을 기다립니다.", "status.scoring": "계가 검토 중입니다. 돌 무리를 표시하거나 현재 점수를 수락하세요.", "status.finished": "종료 · {result}", "status.draw": "무승부 · {result}", "status.takebackHuman": "무르기 요청 중 · LLM 응답을 기다립니다.", "status.takebackLlm": "LLM이 무르기를 요청했습니다 · 응답을 고르세요.", "status.resigned": "{actor}이(가) 기권했습니다 · 대국 종료.", "lastMove.heading": "최근 수", "lastMove.empty": "아직 수가 없습니다", "lastMove.waiting": "첫 수를 기다립니다", "lastMove.meta": "{actor} · {color} · 잡은 돌 {captured}", "history.heading": "수순 기록", "history.count": "{count}수", "history.aria": "현재 대국 수순", "history.empty": "대국을 시작하면 수순이 여기에 표시됩니다.", "history.itemAria": "{ply}수: {move}, {color}, {actor}", "connection.aria": "연결 상태", "connection.label": "연결", "connection.connecting": "확인 중", "connection.connected": "연결됨", "connection.disconnected": "재연결 중", "connection.error": "요청 오류", "score.heading": "계가", "score.live": "진행", "score.review": "검토", "score.final": "최종", "score.black": "흑", "score.white": "백", "score.territoryBlack": "흑 집", "score.territoryWhite": "백 집", "score.komi": "덤", "score.prisoners": "사석", "score.waiting": "패스가 두 번 나오면 계가 수치가 표시됩니다.", "score.modeLabel": "돌 표시", "score.dead": "사석 표시", "score.seki": "빅인 돌 무리", "score.accept": "점수 수락", "score.resume": "대국 재개", "score.accepted": "사람 {human} · LLM {llm}", "score.acceptedShort": "수락", "score.pendingShort": "대기", "score.breakdown": "집: 흑 {black} · 백 {white}", "setup.eyebrow": "새 대국 · 판 설정", "setup.heading": "새 대국 설정", "setup.description": "돌 색과 판 크기를 고르세요. LLM은 별도 CLI에서 둡니다.", "setup.colorLabel": "내 돌", "setup.groupAria": "사람 돌 색 선택", "setup.sizeLabel": "판 크기", "setup.sizeAria": "판 크기 선택", "setup.black.label": "흑으로 두기", "setup.black.detail": "선수입니다", "setup.white.label": "백으로 두기", "setup.white.detail": "LLM이 선수입니다", "setup.size.default": "표준", "setup.size.medium": "중형", "setup.size.small": "빠른 대국", "setup.start": "대국 시작", "takeback.dialog.eyebrow": "게임 동작 · 무르기", "takeback.request.heading": "무르기를 요청할까요?", "takeback.request.description": "LLM에게 {plies}수(제{target}수 포함)를 되돌려 달라고 요청합니다.", "takeback.request.cancel": "취소", "takeback.request.confirm": "요청", "takeback.response.heading": "LLM이 무르기를 요청했습니다", "takeback.response.description": "제{target}수를 포함해 {plies}수를 되돌립니다.", "takeback.response.reject": "거부", "takeback.response.accept": "승인", "takeback.aria": "무르기 동작 대화상자", "resign.dialog.eyebrow": "게임 동작 · 기권", "resign.heading": "이 대국을 기권할까요?", "resign.description": "기권하면 대국이 끝나고 상대가 승리합니다.", "resign.confirm": "기권", "resign.aria": "기권 확인 대화상자", "color.black": "흑", "color.white": "백", "actor.human": "사람", "actor.llm": "LLM", "point.name": "{point}", "point.stone": "{point}, {color} 돌", "point.empty": "{point}, 빈 교차점", "point.legal": "합법 수", "confirm.newGame": "현재 대국을 버리고 새 대국을 시작할까요?", "error.generic": "서버가 예상하지 못한 오류를 반환했습니다. 다시 시도하세요.", "error.connect": "서버에 연결할 수 없습니다.", "error.state": "서버 상태를 읽을 수 없습니다.", "error.move": "수를 보낼 수 없습니다.", "error.start": "새 대국을 시작할 수 없습니다.", "error.score": "계가를 바꿀 수 없습니다.", "error.takeback": "무르기 동작을 보낼 수 없습니다.", "error.resign": "기권할 수 없습니다.", "error.noGame": "진행 중인 대국이 없습니다. 먼저 대국을 시작하세요.", "error.gameOver": "대국이 이미 끝났습니다.", "error.wrongTurn": "지금은 당신의 차례가 아닙니다.", "error.illegalMove": "그 수는 둘 수 없습니다: {move}", "error.invalidColor": "흑 또는 백을 골라 대국을 시작하세요.", "error.invalidBoardSize": "9×9, 13×13, 19×19 중에서 고르세요.", "error.takebackUnavailable": "지금은 무르기를 요청할 수 없습니다.", "error.takebackPending": "이미 응답을 기다리는 무르기 요청이 있습니다.", "error.noPendingTakeback": "응답할 무르기 요청이 없습니다.", "error.resignUnavailable": "지금은 기권할 수 없습니다.", "error.scoreNotScoring": "계가 중에만 계가 동작을 사용할 수 있습니다.", "error.pointRequired": "표시할 돌 무리를 고르세요.", "error.invalidPoint": "이 동작에 사용할 수 없는 교차점입니다.", "error.staleRevision": "계가가 바뀌었습니다. 현재 판을 확인하고 다시 시도하세요.", "error.scoreRevisionRequired": "점수를 수락하려면 화면의 리비전이 필요합니다.", "error.invalidRevision": "리비전은 0 이상의 숫자여야 합니다.", "error.alreadyAccepted": "이미 점수를 수락했습니다. 상대를 기다립니다.", "error.invalidAction": "지금은 그 게임 동작을 사용할 수 없습니다.", "error.gameExists": "이미 진행 중인 대국이 있습니다.",
};
const ERROR_LOCALE_OVERRIDES = {
  ko: { "error.scoreRevisionRequired": "점수를 수락하려면 화면의 리비전이 필요합니다.", "error.invalidRevision": "리비전은 0 이상의 숫자여야 합니다." },
  "zh-Hans": { "error.scoreRevisionRequired": "接受计分需要显示的版本号。", "error.invalidRevision": "版本号必须是非负数。" },
  "zh-Hant": { "error.scoreRevisionRequired": "接受計分需要顯示的版本號。", "error.invalidRevision": "版本號必須是非負數。" },
  ja: { "error.scoreRevisionRequired": "点数の承認には表示中のリビジョンが必要です。", "error.invalidRevision": "リビジョンは0以上の数値で指定してください。" },
  es: { "error.scoreRevisionRequired": "Se necesita la revisión mostrada para aceptar la puntuación.", "error.invalidRevision": "La revisión debe ser un número no negativo." },
  fr: { "error.scoreRevisionRequired": "La révision affichée est requise pour accepter le score.", "error.invalidRevision": "La révision doit être un nombre positif ou nul." },
  de: { "error.scoreRevisionRequired": "Zum Annehmen der Wertung ist die angezeigte Revision nötig.", "error.invalidRevision": "Die Revision muss eine nichtnegative Zahl sein." },
};
const MODE_LOCALE_OVERRIDES = {
  en: {
    "meta.description": "A local baduk workbench for human-vs-LLM games and CLI-vs-CLI spectating.", "setup.description": "Choose a game mode and board size.", "board.caption.cli": "{black} · Black vs {white} · {size}×{size}",
    "clock.cli.label": "CLI TURN", "clock.cli.detail": "Waiting for the {color} move from the CLI.", "status.cliBlack": "{name} is to play Black. Waiting for the CLI response.", "status.cliWhite": "{name} is to play White. Waiting for the CLI response.", "score.acceptedCli": "Black {black} · White {white}",
    "setup.modeLabel": "Game mode", "setup.modeAria": "Game mode selection", "setup.mode.human.label": "Human vs LLM", "setup.mode.human.detail": "Play one side in the browser", "setup.mode.cli.label": "CLI vs CLI", "setup.mode.cli.detail": "Watch two CLI sessions play", "setup.namesLabel": "AI names", "setup.blackName": "Black AI", "setup.whiteName": "White AI", "setup.namePlaceholder": "Optional name", "player.blackDefault": "Black AI", "player.whiteDefault": "White AI",
    "guide.aria": "CLI connection guide", "guide.summary": "Connect the two CLI sessions", "guide.description": "Run one independent CLI session for each color. This browser only watches the shared game.", "guide.commandLabel": "Commands", "guide.promptLabel": "Session prompt", "guide.copyCommand": "Copy commands", "guide.copyPrompt": "Copy prompt", "guide.copied": "Copied", "guide.copyError": "Could not copy the text. Select and copy it manually.", "guide.prompt": "You are the {color} session in a local CLI-vs-CLI baduk game.\n1. Read the play-llm-baduk skill and `baduk --help`.\n2. Wait with `baduk --color {color} wait`, inspect the snapshot, then play with `baduk --color {color} move MOVE`.\n3. Repeat the wait/move loop, keeping the color flag on every command. Use `pass` when appropriate.\n4. Reply to takeback requests with `baduk --color {color} takeback request|accept|reject`. During scoring, review the current revision, use `baduk --color {color} score dead POINT --revision N` or `seki POINT --revision N`, then accept with `baduk --color {color} score accept --revision N`, or resume with `baduk --color {color} score resume`.\n5. Keep the color flag on every participant command, review every new revision before scoring or accepting, and use `baduk --color {color} resign` when appropriate. Stop after a terminal result.\n6. After a reset, reread the skill and help. Keep only one pending wait.",
  },
  ko: {
    "meta.description": "사람 대 LLM 대국과 CLI 대 CLI 관전을 위한 로컬 바둑 워크벤치입니다.", "setup.description": "대국 방식과 판 크기를 고르세요.", "board.caption.cli": "{black} · 흑 대 백 · {white} · {size}×{size}",
    "clock.cli.label": "CLI 차례", "clock.cli.detail": "CLI에서 {color} 수를 보내기를 기다립니다.", "status.cliBlack": "{name}의 흑 차례입니다. CLI 응답을 기다립니다.", "status.cliWhite": "{name}의 백 차례입니다. CLI 응답을 기다립니다.", "score.acceptedCli": "흑 {black} · 백 {white}",
    "setup.modeLabel": "대국 방식", "setup.modeAria": "대국 방식 선택", "setup.mode.human.label": "사람 대 LLM", "setup.mode.human.detail": "브라우저에서 한쪽으로 두기", "setup.mode.cli.label": "CLI 대 CLI", "setup.mode.cli.detail": "두 CLI 세션의 대국 관전", "setup.namesLabel": "AI 이름", "setup.blackName": "흑 AI", "setup.whiteName": "백 AI", "setup.namePlaceholder": "이름 선택 사항", "player.blackDefault": "흑 AI", "player.whiteDefault": "백 AI",
    "guide.aria": "CLI 연결 안내", "guide.summary": "두 CLI 세션 연결", "guide.description": "색마다 독립된 CLI 세션을 하나씩 실행하세요. 이 브라우저는 공유 대국을 관전합니다.", "guide.commandLabel": "명령", "guide.promptLabel": "세션 프롬프트", "guide.copyCommand": "명령 복사", "guide.copyPrompt": "프롬프트 복사", "guide.copied": "복사됨", "guide.copyError": "텍스트를 복사할 수 없습니다. 직접 선택해 복사하세요.", "guide.prompt": "로컬 CLI 대 CLI 바둑 대국의 {color} 세션입니다.\n1. play-llm-baduk 스킬과 `baduk --help`를 읽으세요.\n2. `baduk --color {color} wait`로 기다리고 스냅샷을 확인한 뒤 `baduk --color {color} move MOVE`로 두세요.\n3. 모든 명령에 색 플래그를 유지하며 기다리기와 두기 과정을 반복하세요. 필요하면 `pass`를 사용하세요.\n4. 무르기 요청에는 `baduk --color {color} takeback request|accept|reject`로 응답하세요. 계가 중에는 현재 리비전을 확인하고 `baduk --color {color} score dead POINT --revision N` 또는 `seki POINT --revision N`으로 표시한 뒤 `baduk --color {color} score accept --revision N`으로 수락하거나 `baduk --color {color} score resume`으로 대국을 재개하세요.\n5. 모든 참가자 명령에 색 플래그를 유지하고, 계가나 수락 전에 새 리비전을 확인하세요. 필요하면 `baduk --color {color} resign`을 사용하세요. 종료 결과가 나오면 멈추세요.\n6. 초기화 뒤 스킬과 도움말을 다시 읽으세요. 대기 요청은 한 번만 유지하세요.",
  },
  "zh-Hans": {
    "meta.description": "用于人类对 LLM 对局和 CLI 对 CLI 观战的本地围棋工作台。", "setup.description": "选择对局模式和棋盘大小。", "board.caption.cli": "{black} · 黑方对 {white} · {size}×{size}",
    "clock.cli.label": "CLI 回合", "clock.cli.detail": "等待 CLI 发送{color}棋。", "status.cliBlack": "{name}执黑。等待 CLI 响应。", "status.cliWhite": "{name}执白。等待 CLI 响应。", "score.acceptedCli": "黑 {black} · 白 {white}",
    "setup.modeLabel": "对局模式", "setup.modeAria": "对局模式选择", "setup.mode.human.label": "人类对 LLM", "setup.mode.human.detail": "在浏览器中执一方", "setup.mode.cli.label": "CLI 对 CLI", "setup.mode.cli.detail": "观看两个 CLI 会话对局", "setup.namesLabel": "AI 名称", "setup.blackName": "黑方 AI", "setup.whiteName": "白方 AI", "setup.namePlaceholder": "可选名称", "player.blackDefault": "黑方 AI", "player.whiteDefault": "白方 AI",
    "guide.aria": "CLI 连接指南", "guide.summary": "连接两个 CLI 会话", "guide.description": "为每种棋色运行一个独立的 CLI 会话。浏览器只观看共享对局。", "guide.commandLabel": "命令", "guide.promptLabel": "会话提示词", "guide.copyCommand": "复制命令", "guide.copyPrompt": "复制提示词", "guide.copied": "已复制", "guide.copyError": "无法复制文本，请手动选择并复制。", "guide.prompt": "你是本地 CLI 对 CLI 围棋对局的{color}会话。\n1. 阅读 play-llm-baduk 技能和 `baduk --help`。\n2. 使用 `baduk --color {color} wait` 等待，查看快照，然后使用 `baduk --color {color} move MOVE` 落子。\n3. 重复等待和落子循环，每条命令都保留棋色参数。需要时使用 `pass`。\n4. 使用 `baduk --color {color} takeback request|accept|reject` 回复悔棋请求。计分时查看当前版本，使用 `baduk --color {color} score dead POINT --revision N` 或 `baduk --color {color} score seki POINT --revision N` 标记死子或双活，再使用 `baduk --color {color} score accept --revision N` 接受，或使用 `baduk --color {color} score resume` 继续对局。\n5. 每条参与者命令都保留棋色参数，在计分或接受前查看每个新版本，需要时使用 `baduk --color {color} resign`。出现终局结果后停止。\n6. 重置后重新阅读技能和帮助。只保留一个待处理的等待请求。",
  },
  "zh-Hant": {
    "meta.description": "用於人類對 LLM 對局和 CLI 對 CLI 觀戰的本地圍棋工作台。", "setup.description": "選擇對局模式和棋盤大小。", "board.caption.cli": "{black} · 黑方對 {white} · {size}×{size}",
    "clock.cli.label": "CLI 回合", "clock.cli.detail": "等待 CLI 傳送{color}棋。", "status.cliBlack": "{name}執黑。等待 CLI 回應。", "status.cliWhite": "{name}執白。等待 CLI 回應。", "score.acceptedCli": "黑 {black} · 白 {white}",
    "setup.modeLabel": "對局模式", "setup.modeAria": "對局模式選擇", "setup.mode.human.label": "人類對 LLM", "setup.mode.human.detail": "在瀏覽器執一方", "setup.mode.cli.label": "CLI 對 CLI", "setup.mode.cli.detail": "觀看兩個 CLI 工作階段對局", "setup.namesLabel": "AI 名稱", "setup.blackName": "黑方 AI", "setup.whiteName": "白方 AI", "setup.namePlaceholder": "可選名稱", "player.blackDefault": "黑方 AI", "player.whiteDefault": "白方 AI",
    "guide.aria": "CLI 連線指南", "guide.summary": "連線兩個 CLI 工作階段", "guide.description": "為每種棋色執行一個獨立的 CLI 工作階段。瀏覽器只觀看共享對局。", "guide.commandLabel": "指令", "guide.promptLabel": "工作階段提示詞", "guide.copyCommand": "複製指令", "guide.copyPrompt": "複製提示詞", "guide.copied": "已複製", "guide.copyError": "無法複製文字，請手動選取並複製。", "guide.prompt": "你是本地 CLI 對 CLI 圍棋對局的{color}工作階段。\n1. 閱讀 play-llm-baduk 技能和 `baduk --help`。\n2. 使用 `baduk --color {color} wait` 等待，查看快照，再使用 `baduk --color {color} move MOVE` 落子。\n3. 重複等待和落子循環，每個指令都保留棋色參數。需要時使用 `pass`。\n4. 使用 `baduk --color {color} takeback request|accept|reject` 回覆悔棋請求。計分時查看目前版本，使用 `baduk --color {color} score dead POINT --revision N` 或 `baduk --color {color} score seki POINT --revision N` 標記死子或雙活，再使用 `baduk --color {color} score accept --revision N` 接受，或使用 `baduk --color {color} score resume` 繼續對局。\n5. 每個參與者指令都保留棋色參數，在計分或接受前查看每個新版本，需要時使用 `baduk --color {color} resign`。出現終局結果後停止。\n6. 重設後重新閱讀技能和說明。只保留一個待處理的等待請求。",
  },
  ja: {
    "meta.description": "人間対LLMの対局とCLI対CLIの観戦に対応したローカル囲碁ワークベンチです。", "setup.description": "対局モードと盤のサイズを選んでください。", "board.caption.cli": "{black} · 黒対 {white} · {size}×{size}",
    "clock.cli.label": "CLIの手番", "clock.cli.detail": "CLIから{color}の着手を待っています。", "status.cliBlack": "{name}の黒番です。CLIの応答を待っています。", "status.cliWhite": "{name}の白番です。CLIの応答を待っています。", "score.acceptedCli": "黒 {black} · 白 {white}",
    "setup.modeLabel": "対局モード", "setup.modeAria": "対局モードの選択", "setup.mode.human.label": "人間 対 LLM", "setup.mode.human.detail": "ブラウザで片方を打つ", "setup.mode.cli.label": "CLI 対 CLI", "setup.mode.cli.detail": "2つのCLIセッションを観戦", "setup.namesLabel": "AI名", "setup.blackName": "黒AI", "setup.whiteName": "白AI", "setup.namePlaceholder": "任意の名前", "player.blackDefault": "黒AI", "player.whiteDefault": "白AI",
    "guide.aria": "CLI接続ガイド", "guide.summary": "2つのCLIセッションを接続", "guide.description": "各色に1つずつ独立したCLIセッションを実行します。このブラウザは共有対局を観戦します。", "guide.commandLabel": "コマンド", "guide.promptLabel": "セッション用プロンプト", "guide.copyCommand": "コマンドをコピー", "guide.copyPrompt": "プロンプトをコピー", "guide.copied": "コピーしました", "guide.copyError": "コピーできません。手動で選択してコピーしてください。", "guide.prompt": "ローカルCLI対CLIの囲碁対局で{color}を担当するセッションです。\n1. play-llm-badukスキルと `baduk --help` を読んでください。\n2. `baduk --color {color} wait` で待ち、スナップショットを確認して `baduk --color {color} move MOVE` で着手します。\n3. 各コマンドに色フラグを付けて待機と着手を繰り返します。必要に応じて `pass` を使います。\n4. 待ったの要求には対応する待ったコマンドで返答します。計算中は現在のリビジョンを確認し、死石やセキをマークして、表示された `--revision N` で承認するか対局を再開します。\n5. 承認や計算の前に新しいリビジョンを確認します。終局結果が出たら停止します。\n6. リセット後はスキルとヘルプを読み直します。待機は1件だけにします。",
  },
  es: {
    "meta.description": "Un espacio local de baduk para partidas humano contra LLM y observación CLI contra CLI.", "setup.description": "Elige el modo de partida y el tamaño del tablero.", "board.caption.cli": "{black} · Negras contra {white} · {size}×{size}",
    "clock.cli.label": "TURNO DEL CLI", "clock.cli.detail": "Esperando la jugada {color} desde el CLI.", "status.cliBlack": "Turno de negras para {name}. Esperando la respuesta del CLI.", "status.cliWhite": "Turno de blancas para {name}. Esperando la respuesta del CLI.", "score.acceptedCli": "Negras {black} · Blancas {white}",
    "setup.modeLabel": "Modo de partida", "setup.modeAria": "Selección del modo de partida", "setup.mode.human.label": "Humano contra LLM", "setup.mode.human.detail": "Juega un lado en el navegador", "setup.mode.cli.label": "CLI contra CLI", "setup.mode.cli.detail": "Observa dos sesiones CLI", "setup.namesLabel": "Nombres de las IA", "setup.blackName": "IA de negras", "setup.whiteName": "IA de blancas", "setup.namePlaceholder": "Nombre opcional", "player.blackDefault": "IA de negras", "player.whiteDefault": "IA de blancas",
    "guide.aria": "Guía de conexión CLI", "guide.summary": "Conectar las dos sesiones CLI", "guide.description": "Ejecuta una sesión CLI independiente para cada color. Este navegador solo observa la partida compartida.", "guide.commandLabel": "Comandos", "guide.promptLabel": "Indicación de sesión", "guide.copyCommand": "Copiar comandos", "guide.copyPrompt": "Copiar indicación", "guide.copied": "Copiado", "guide.copyError": "No se pudo copiar el texto. Selecciónalo y cópialo manualmente.", "guide.prompt": "Eres la sesión de {color} en una partida local de baduk CLI contra CLI.\n1. Lee la habilidad play-llm-baduk y `baduk --help`.\n2. Espera con `baduk --color {color} wait`, revisa la instantánea y juega con `baduk --color {color} move MOVE`.\n3. Repite el ciclo de espera y jugada, conservando el indicador de color en cada comando. Usa `pass` cuando corresponda.\n4. Responde a las solicitudes de deshacer con el comando correspondiente. Durante la puntuación, revisa la revisión actual, marca grupos muertos o seki, acepta con el `--revision N` mostrado o reanuda la partida.\n5. Revisa cada revisión nueva antes de puntuar o aceptar. Detente tras un resultado terminal.\n6. Después de reiniciar, vuelve a leer la habilidad y la ayuda. Mantén una sola espera pendiente.",
  },
  fr: {
    "meta.description": "Un espace local de go pour jouer humain contre LLM et observer une partie CLI contre CLI.", "setup.description": "Choisissez le mode de partie et la taille du plateau.", "board.caption.cli": "{black} · Noirs contre {white} · {size}×{size}",
    "clock.cli.label": "TOUR DU CLI", "clock.cli.detail": "En attente du coup {color} depuis le CLI.", "status.cliBlack": "{name} joue les noirs. En attente de la réponse du CLI.", "status.cliWhite": "{name} joue les blancs. En attente de la réponse du CLI.", "score.acceptedCli": "Noirs {black} · Blancs {white}",
    "setup.modeLabel": "Mode de partie", "setup.modeAria": "Sélection du mode de partie", "setup.mode.human.label": "Humain contre LLM", "setup.mode.human.detail": "Jouez un camp dans le navigateur", "setup.mode.cli.label": "CLI contre CLI", "setup.mode.cli.detail": "Observez deux sessions CLI", "setup.namesLabel": "Noms des IA", "setup.blackName": "IA noire", "setup.whiteName": "IA blanche", "setup.namePlaceholder": "Nom facultatif", "player.blackDefault": "IA noire", "player.whiteDefault": "IA blanche",
    "guide.aria": "Guide de connexion CLI", "guide.summary": "Connecter les deux sessions CLI", "guide.description": "Lancez une session CLI indépendante pour chaque couleur. Ce navigateur observe la partie partagée.", "guide.commandLabel": "Commandes", "guide.promptLabel": "Invite de session", "guide.copyCommand": "Copier les commandes", "guide.copyPrompt": "Copier l'invite", "guide.copied": "Copié", "guide.copyError": "Impossible de copier le texte. Sélectionnez-le et copiez-le manuellement.", "guide.prompt": "Vous êtes la session {color} d'une partie locale de go CLI contre CLI.\n1. Lisez la compétence play-llm-baduk et `baduk --help`.\n2. Attendez avec `baduk --color {color} wait`, consultez l'instantané, puis jouez avec `baduk --color {color} move MOVE`.\n3. Répétez la boucle attente-coup en gardant l'option de couleur dans chaque commande. Utilisez `pass` lorsque c'est approprié.\n4. Répondez aux demandes d'annulation avec la commande correspondante. Pendant le décompte, vérifiez la révision actuelle, marquez les groupes morts ou seki, acceptez avec le `--revision N` affiché ou reprenez la partie.\n5. Vérifiez chaque nouvelle révision avant le décompte ou l'acceptation. Arrêtez-vous après un résultat final.\n6. Après une réinitialisation, relisez la compétence et l'aide. Ne gardez qu'une seule attente en cours.",
  },
  de: {
    "meta.description": "Eine lokale Go-Werkbank für Mensch-gegen-LLM-Partien und CLI-gegen-CLI-Beobachtung.", "setup.description": "Spielmodus und Brettgröße wählen.", "board.caption.cli": "{black} · Schwarz gegen {white} · {size}×{size}",
    "clock.cli.label": "CLI AM ZUG", "clock.cli.detail": "Warte auf den {color} Zug aus dem CLI.", "status.cliBlack": "{name} ist mit Schwarz am Zug. Warte auf die CLI-Antwort.", "status.cliWhite": "{name} ist mit Weiß am Zug. Warte auf die CLI-Antwort.", "score.acceptedCli": "Schwarz {black} · Weiß {white}",
    "setup.modeLabel": "Spielmodus", "setup.modeAria": "Auswahl des Spielmodus", "setup.mode.human.label": "Mensch gegen LLM", "setup.mode.human.detail": "Eine Seite im Browser spielen", "setup.mode.cli.label": "CLI gegen CLI", "setup.mode.cli.detail": "Zwei CLI-Sitzungen beobachten", "setup.namesLabel": "KI-Namen", "setup.blackName": "Schwarze KI", "setup.whiteName": "Weiße KI", "setup.namePlaceholder": "Optionaler Name", "player.blackDefault": "Schwarze KI", "player.whiteDefault": "Weiße KI",
    "guide.aria": "CLI-Verbindungsleitfaden", "guide.summary": "Die zwei CLI-Sitzungen verbinden", "guide.description": "Eine unabhängige CLI-Sitzung für jede Farbe starten. Dieser Browser beobachtet die gemeinsame Partie.", "guide.commandLabel": "Befehle", "guide.promptLabel": "Sitzungsaufforderung", "guide.copyCommand": "Befehle kopieren", "guide.copyPrompt": "Aufforderung kopieren", "guide.copied": "Kopiert", "guide.copyError": "Text konnte nicht kopiert werden. Manuell auswählen und kopieren.", "guide.prompt": "Du bist die {color}-Sitzung in einer lokalen CLI-gegen-CLI-Go-Partie.\n1. Lies den play-llm-baduk-Skill und `baduk --help`.\n2. Warte mit `baduk --color {color} wait`, prüfe den Snapshot und spiele mit `baduk --color {color} move MOVE`.\n3. Wiederhole die Warte-Zug-Schleife und führe das Farbargument in jedem Befehl mit. Nutze bei Bedarf `pass`.\n4. Antworte auf Rücknahmeanfragen mit dem passenden Rücknahmebefehl. Prüfe bei der Wertung die aktuelle Revision, markiere tote oder Seki-Gruppen, akzeptiere mit der angezeigten `--revision N` oder setze das Spiel fort.\n5. Prüfe jede neue Revision vor Wertung oder Annahme. Stoppe nach einem Endergebnis.\n6. Lies Skill und Hilfe nach einem Reset erneut. Halte nur eine offene Warteanfrage.",
  },
};
/** @description 대국 방식과 관전자 상태에 공통으로 쓰는 승인된 AI 중심 문구입니다. */
const SPECTATOR_UI_OVERRIDES = {
  en: {
    "brand.tagline": "LOCAL BADUK · SHARED BOARD", "setup.mode.human.label": "Human vs AI", "setup.mode.cli.label": "AI vs AI", "guide.aria": "AI connection guide", "guide.summary": "Connect the two AI sessions",
    "status.takebackCli": "{requesterColor} {requesterName} requested a takeback · Waiting for {responderColor} {responderName}.", "clock.takeback.cliValue": "{name} to reply", "clock.takeback.cliDetail": "{requesterColor} {requesterName} requested a takeback. Waiting for {responderColor} {responderName}.",
    "status.scoringCli": "The two AI sessions are reviewing the score: Black {black} · White {white}.", "clock.scoring.cliValue": "REVIEWING", "clock.scoring.cliDetail": "The two AI sessions are reviewing the score: Black {black} · White {white}.",
    "status.finishedCli": "Black {black} · White {white} · Finished · {result}", "status.drawCli": "Black {black} · White {white} · Draw · {result}", "clock.finished.cliDetail": "Black {black} and White {white} accepted the score.",
  },
  ko: {
    "brand.tagline": "로컬 바둑 · 공유 바둑판", "setup.mode.human.label": "사람 대 AI", "setup.mode.cli.label": "AI 대 AI", "guide.aria": "AI 연결 안내", "guide.summary": "두 AI 연결",
    "status.takebackCli": "{requesterColor} {requesterName}이(가) 무르기를 요청했습니다 · {responderColor} {responderName}의 응답을 기다립니다.", "clock.takeback.cliValue": "{name} 응답", "clock.takeback.cliDetail": "{requesterColor} {requesterName}이(가) 무르기를 요청했습니다. {responderColor} {responderName}의 응답을 기다립니다.",
    "status.scoringCli": "두 AI가 계가를 검토하고 있습니다: 흑 {black} · 백 {white}.", "clock.scoring.cliValue": "검토 중", "clock.scoring.cliDetail": "두 AI가 계가를 검토하고 있습니다: 흑 {black} · 백 {white}.",
    "status.finishedCli": "흑 {black} · 백 {white} · 종료 · {result}", "status.drawCli": "흑 {black} · 백 {white} · 무승부 · {result}", "clock.finished.cliDetail": "흑 {black}과 백 {white}가 계가를 수락했습니다.",
  },
  "zh-Hans": {
    "brand.tagline": "本地围棋 · 共享棋盘", "setup.mode.human.label": "人类对 AI", "setup.mode.cli.label": "AI 对 AI", "guide.aria": "AI 连接指南", "guide.summary": "连接两个 AI 会话",
    "status.takebackCli": "{requesterColor}{requesterName}请求悔棋 · 等待{responderColor}{responderName}回应。", "clock.takeback.cliValue": "等待{name}回应", "clock.takeback.cliDetail": "{requesterColor}{requesterName}请求悔棋。等待{responderColor}{responderName}回应。",
    "status.scoringCli": "两个 AI 会话正在复核计分：黑方 {black} · 白方 {white}。", "clock.scoring.cliValue": "复核中", "clock.scoring.cliDetail": "两个 AI 会话正在复核计分：黑方 {black} · 白方 {white}。",
    "status.finishedCli": "黑方 {black} · 白方 {white} · 对局结束 · {result}", "status.drawCli": "黑方 {black} · 白方 {white} · 和棋 · {result}", "clock.finished.cliDetail": "黑方 {black}和白方 {white}已接受计分。",
  },
  "zh-Hant": {
    "brand.tagline": "本地圍棋 · 共用棋盤", "setup.mode.human.label": "人類對 AI", "setup.mode.cli.label": "AI 對 AI", "guide.aria": "AI 連線指南", "guide.summary": "連線兩個 AI 工作階段",
    "status.takebackCli": "{requesterColor}{requesterName}請求悔棋 · 等待{responderColor}{responderName}回覆。", "clock.takeback.cliValue": "等待{name}回覆", "clock.takeback.cliDetail": "{requesterColor}{requesterName}請求悔棋。等待{responderColor}{responderName}回覆。",
    "status.scoringCli": "兩個 AI 工作階段正在檢查計分：黑方 {black} · 白方 {white}。", "clock.scoring.cliValue": "檢查中", "clock.scoring.cliDetail": "兩個 AI 工作階段正在檢查計分：黑方 {black} · 白方 {white}。",
    "status.finishedCli": "黑方 {black} · 白方 {white} · 對局結束 · {result}", "status.drawCli": "黑方 {black} · 白方 {white} · 和棋 · {result}", "clock.finished.cliDetail": "黑方 {black}和白方 {white}已接受計分。",
  },
  ja: {
    "brand.tagline": "ローカル囲碁 · 共有盤", "setup.mode.human.label": "人間 対 AI", "setup.mode.cli.label": "AI 対 AI", "guide.aria": "AI接続ガイド", "guide.summary": "2つのAIセッションを接続",
    "status.takebackCli": "{requesterColor} {requesterName}が待ったを求めました · {responderColor} {responderName}の返答を待っています。", "clock.takeback.cliValue": "{name}の返答", "clock.takeback.cliDetail": "{requesterColor} {requesterName}が待ったを求めました。{responderColor} {responderName}の返答を待っています。",
    "status.scoringCli": "2つのAIセッションが整地を確認中です：黒 {black} · 白 {white}。", "clock.scoring.cliValue": "確認中", "clock.scoring.cliDetail": "2つのAIセッションが整地を確認中です：黒 {black} · 白 {white}。",
    "status.finishedCli": "黒 {black} · 白 {white} · 対局終了 · {result}", "status.drawCli": "黒 {black} · 白 {white} · 引き分け · {result}", "clock.finished.cliDetail": "黒 {black}と白 {white}が点数を承認しました。",
  },
  es: {
    "brand.tagline": "GO LOCAL · TABLERO COMPARTIDO", "setup.mode.human.label": "Humano contra IA", "setup.mode.cli.label": "IA contra IA", "guide.aria": "Guía de conexión de IA", "guide.summary": "Conectar las dos sesiones de IA",
    "status.takebackCli": "{requesterColor} {requesterName} solicitó deshacer · Esperando a {responderColor} {responderName}.", "clock.takeback.cliValue": "Respuesta de {name}", "clock.takeback.cliDetail": "{requesterColor} {requesterName} solicitó deshacer. Esperando a {responderColor} {responderName}.",
    "status.scoringCli": "Las dos sesiones de IA revisan la puntuación: negras {black} · blancas {white}.", "clock.scoring.cliValue": "REVISANDO", "clock.scoring.cliDetail": "Las dos sesiones de IA revisan la puntuación: negras {black} · blancas {white}.",
    "status.finishedCli": "Negras {black} · Blancas {white} · Finalizada · {result}", "status.drawCli": "Negras {black} · Blancas {white} · Tablas · {result}", "clock.finished.cliDetail": "Negras {black} y blancas {white} aceptaron la puntuación.",
  },
  fr: {
    "brand.tagline": "GO LOCAL · PLATEAU PARTAGÉ", "setup.mode.human.label": "Humain contre IA", "setup.mode.cli.label": "IA contre IA", "guide.aria": "Guide de connexion des IA", "guide.summary": "Connecter les deux sessions d'IA",
    "status.takebackCli": "{requesterColor} {requesterName} demande l'annulation · En attente de {responderColor} {responderName}.", "clock.takeback.cliValue": "Réponse de {name}", "clock.takeback.cliDetail": "{requesterColor} {requesterName} demande l'annulation. En attente de {responderColor} {responderName}.",
    "status.scoringCli": "Les deux sessions d'IA vérifient le score : noirs {black} · blancs {white}.", "clock.scoring.cliValue": "VÉRIFICATION", "clock.scoring.cliDetail": "Les deux sessions d'IA vérifient le score : noirs {black} · blancs {white}.",
    "status.finishedCli": "Noirs {black} · Blancs {white} · Partie terminée · {result}", "status.drawCli": "Noirs {black} · Blancs {white} · Égalité · {result}", "clock.finished.cliDetail": "Noirs {black} et blancs {white} ont accepté le score.",
  },
  de: {
    "brand.tagline": "LOKALES GO · GEMEINSAMES BRETT", "setup.mode.human.label": "Mensch gegen KI", "setup.mode.cli.label": "KI gegen KI", "guide.aria": "KI-Verbindungsleitfaden", "guide.summary": "Die zwei KI-Sitzungen verbinden",
    "status.takebackCli": "{requesterColor} {requesterName} beantragt eine Rücknahme · Warte auf {responderColor} {responderName}.", "clock.takeback.cliValue": "Antwort von {name}", "clock.takeback.cliDetail": "{requesterColor} {requesterName} beantragt eine Rücknahme. Warte auf {responderColor} {responderName}.",
    "status.scoringCli": "Die zwei KI-Sitzungen prüfen die Wertung: Schwarz {black} · Weiß {white}.", "clock.scoring.cliValue": "PRÜFUNG", "clock.scoring.cliDetail": "Die zwei KI-Sitzungen prüfen die Wertung: Schwarz {black} · Weiß {white}.",
    "status.finishedCli": "Schwarz {black} · Weiß {white} · Beendet · {result}", "status.drawCli": "Schwarz {black} · Weiß {white} · Unentschieden · {result}", "clock.finished.cliDetail": "Schwarz {black} und Weiß {white} haben die Wertung angenommen.",
  },
};
/** @description 초기화 뒤 참가자 세션이 최신 상태를 다시 읽도록 안내합니다. */
const GUIDE_RESET_OVERRIDES = {
  en: { "guide.resetStatus": "After a reset, reread the current status with `baduk --color {color} status`." },
  ko: { "guide.resetStatus": "초기화 뒤 `baduk --color {color} status`로 현재 상태를 다시 확인하세요." },
  "zh-Hans": { "guide.resetStatus": "重置后，使用 `baduk --color {color} status` 重新查看当前状态。" },
  "zh-Hant": { "guide.resetStatus": "重設後，使用 `baduk --color {color} status` 重新查看目前狀態。" },
  ja: { "guide.resetStatus": "リセット後は `baduk --color {color} status` で現在の状態を読み直してください。" },
  es: { "guide.resetStatus": "Después de reiniciar, vuelve a consultar el estado actual con `baduk --color {color} status`." },
  fr: { "guide.resetStatus": "Après une réinitialisation, relisez l'état actuel avec `baduk --color {color} status`." },
  de: { "guide.resetStatus": "Lies nach einem Reset den aktuellen Status mit `baduk --color {color} status` erneut ein." },
};
const CATALOGS = Object.fromEntries(SUPPORTED_LOCALES.map((locale) => [locale, { ...ENGLISH_CATALOG, ...(CATALOG_OVERRIDES[locale] || {}), ...(COMMON_LOCALE_OVERRIDES[locale] || {}), ...(locale === "ko" ? KOREAN_LOCALE_OVERRIDES : {}), ...(ERROR_LOCALE_OVERRIDES[locale] || {}), ...(MODE_LOCALE_OVERRIDES[locale] || {}), ...(SPECTATOR_UI_OVERRIDES[locale] || {}), ...(GUIDE_RESET_OVERRIDES[locale] || {}) }]));
const ERROR_KEYS = {
  no_game: "error.noGame", game_over: "error.gameOver", wrong_turn: "error.wrongTurn", illegal_move: "error.illegalMove",
  invalid_color: "error.invalidColor", invalid_board_size: "error.invalidBoardSize", game_exists: "error.gameExists",
  takeback_no_move: "error.takebackUnavailable", takeback_unavailable: "error.takebackUnavailable", cannot_takeback: "error.takebackUnavailable",
  takeback_pending: "error.takebackPending", takeback_move_blocked: "error.takebackPending", takeback_own_request: "error.takebackPending", takeback_no_pending: "error.noPendingTakeback",
  no_pending_takeback: "error.noPendingTakeback", resign_unavailable: "error.resignUnavailable", cannot_resign: "error.resignUnavailable",
  scoring_not_active: "error.scoreNotScoring", score_not_scoring: "error.scoreNotScoring", not_scoring: "error.scoreNotScoring",
  score_point_required: "error.pointRequired", point_required: "error.pointRequired", score_point_invalid: "error.invalidPoint", invalid_point: "error.invalidPoint",
  score_revision_required: "error.scoreRevisionRequired", stale_revision: "error.staleRevision", invalid_revision: "error.invalidRevision",
  already_accepted: "error.alreadyAccepted", score_action_invalid: "error.invalidAction", invalid_action: "error.invalidAction",
};

let currentLocale = "en";
const listeners = new Set();

/** @description 로케일 태그를 지원 목록의 이름으로 정규화합니다. */
function mapLocale(tag) {
  const normalized = String(tag || "").toLowerCase();
  if (normalized === "ko" || normalized.startsWith("ko-")) return "ko";
  if (normalized === "zh-tw" || normalized === "zh-hk" || normalized === "zh-hant") return "zh-Hant";
  if (normalized === "zh" || normalized === "zh-cn" || normalized === "zh-sg" || normalized === "zh-hans") return "zh-Hans";
  if (normalized === "ja" || normalized.startsWith("ja-")) return "ja";
  if (normalized === "es" || normalized.startsWith("es-")) return "es";
  if (normalized === "fr" || normalized.startsWith("fr-")) return "fr";
  if (normalized === "de" || normalized.startsWith("de-")) return "de";
  if (normalized === "en" || normalized.startsWith("en-")) return "en";
  return null;
}

/** @description 저장소와 브라우저 선호 언어로 초기 로케일을 결정합니다. */
function detectLocale() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (SUPPORTED_LOCALES.includes(stored)) return stored;
  } catch {
    // 저장소를 사용할 수 없어도 현재 탭의 언어 선택은 계속 동작합니다.
  }
  const candidates = Array.isArray(navigator.languages) ? [...navigator.languages] : [];
  if (navigator.language && !candidates.includes(navigator.language)) candidates.push(navigator.language);
  for (const candidate of candidates) {
    const locale = mapLocale(candidate);
    if (locale) return locale;
  }
  return "en";
}

/** @description 문자열의 자리표시자를 번역 값으로 치환합니다. */
function interpolate(template, values) {
  return template.replace(/\{([a-zA-Z0-9_.-]+)\}/g, (match, key) => Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match);
}

/** @description 현재 카탈로그에서 문구를 반환합니다. */
function translate(key, values = {}) {
  const template = CATALOGS[currentLocale][key];
  if (typeof template !== "string") throw new Error(`Missing i18n key: ${key}`);
  return interpolate(template, values);
}

/** @description 서버 오류를 언어 변경 가능한 오류 상태로 바꿉니다. */
function serverError(detail) {
  const code = detail && typeof detail === "object" ? detail.code : null;
  const key = ERROR_KEYS[code] || "error.generic";
  const values = code === "illegal_move" && detail.message
    ? { move: detail.message.replace(/^Illegal move:\s*/i, "") }
    : { code: code || "unknown" };
  const error = new Error(code || "server_error");
  error.i18n = { key, values };
  return error;
}

/** @description 로케일을 저장하고 화면 갱신 리스너를 호출합니다. */
function setLocale(locale) {
  if (!SUPPORTED_LOCALES.includes(locale)) return false;
  currentLocale = locale;
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // 저장소가 막혀도 현재 탭에서는 선택한 언어를 사용합니다.
  }
  document.documentElement.lang = locale;
  document.title = translate("meta.title");
  document.querySelector('meta[name="description"]').content = translate("meta.description");
  listeners.forEach((listener) => listener(locale));
  return true;
}

currentLocale = detectLocale();
document.documentElement.lang = currentLocale;

window.LlmBadukI18n = Object.freeze({
  languageOptions: LANGUAGE_OPTIONS,
  supportedLocales: SUPPORTED_LOCALES,
  getLocale: () => currentLocale,
  setLocale,
  subscribe: (listener) => { listeners.add(listener); return () => listeners.delete(listener); },
  t: translate,
  serverError,
});

document.title = translate("meta.title");
document.querySelector('meta[name="description"]').content = translate("meta.description");
