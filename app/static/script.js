const $ = (s) => document.querySelector(s);
let state = {
  file: null,
  demo: false,
  profile: "hosts",
  criticality: "all",
  labels: true,
  tab: "diagram",
  generated: false,
}; // sessionStorage может быть недоступен при file:// — обработка этого случая ниже.
const pages = {
  home: "index.html",
  upload: "upload.html",
  settings: "settings.html",
  results: "results.html",
};
function saveState() {
  try {
    const file = state.file
      ? { name: state.file.name, size: state.file.size }
      : null;
    sessionStorage.setItem(
      "netforma-state",
      JSON.stringify({ ...state, file }),
    );
  } catch {
    /* Интерфейс остаётся работоспособным без сохранения. */
  }
}
function go(page) {
  saveState();
  window.location.href = pages[page];
}
try {
  const saved = JSON.parse(sessionStorage.getItem("netforma-state") || "null");
  if (saved && typeof saved === "object") {
    state = { ...state, ...saved };
    if (!["hosts", "services", "critical"].includes(state.profile))
      state.profile = "hosts";
    if (!["all", "high", "medium"].includes(state.criticality))
      state.criticality = "all";
    if (!["diagram", "code"].includes(state.tab)) state.tab = "diagram";
  }
} 
catch {
  /* Используем настройки по умолчанию. */
}
const titles = {
  home: "Обзор",
  upload: "Загрузка файла",
  settings: "Настройки",
  results: "Результаты",
};
const profiles = {
  hosts: "По хостам",
  services: "По сервисам",
  critical: "По критичности",
};
const example = {
  hosts: [
    { id: "web", name: "Веб-сервер", ip: "10.0.1.10" },
    { id: "app", name: "Сервер приложений", ip: "10.0.1.20" },
    { id: "db", name: "База данных", ip: "10.0.2.10" },
  ],
  services: [
    { name: "Nginx", host: "web" },
    { name: "API", host: "app" },
    { name: "PostgreSQL", host: "db" },
  ],
  connections: [
    { from: "web", to: "app", port: 8080, criticality: "medium" },
    { from: "app", to: "db", port: 5432, criticality: "high" },
  ],
};
function steps(n) {
  return `<div class="steps"><span class="${n >= 1 ? "on" : ""}"><b>1</b>Загрузка файла</span><i></i><span class="${n >= 2 ? "on" : ""}"><b>2</b>Настройки схемы</span><i></i><span class="${n >= 3 ? "on" : ""}"><b>3</b>Результаты</span></div>`;
}
function head(k, title, sub, action = "") {
  return `<div class="pagehead"><div><div class="eyebrow">${k}</div><h1>${title}</h1><p>${sub}</p></div>${action}</div>`;
}
function toast(t) {
  $("#toast").textContent = t;
  $("#toast").style.display = "block";
  setTimeout(() => ($("#toast").style.display = "none"), 3500);
}
function download(name, text, type = "text/plain") {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function getServerResult() {
  try {
    return JSON.parse(
      sessionStorage.getItem("netforma-result") || "null"
    );
  } catch {
    return null;
  }
}
// Главная иллюстрация не содержит IP и портов. Результат показывает учебные данные.
function diagram(hero = false) {
  const service = !hero && state.profile === "services";
  const critical = !hero && state.profile === "critical";
  const onlyHigh = !hero && state.criticality === "high";
  const labels = service
    ? ["Nginx", "API", "PostgreSQL"]
    : ["Веб-сервер", "Сервер приложений", "База данных"];
  const xs = [49, 302, 555];
  const nodes = labels
    .map(
      (label, i) => `<g>
    <rect x="${xs[i]}" y="101" width="175" height="104" rx="11" fill="${critical && i > 0 ? "#9CA3AF" : i === 1 ? "#C7D2FE" : "#E0E7FF"}" stroke="#A5B4FC"/>
    <text x="${xs[i] + 87.5}" y="${hero ? 158 : 151}" text-anchor="middle" fill="#252B3A" font-size="${hero ? 12 : 13}" font-weight="700">${label}</text>
    ${hero ? "" : `<text x="${xs[i] + 87.5}" y="174" text-anchor="middle" fill="#6B7280" font-size="11">${["10.0.1.10", "10.0.1.20", "10.0.2.10"][i]}</text>`}
  </g>`,
    )
    .join("");
  const arrow = (x, port) =>
    `<path d="M${x} 153 H${x + 78} m-7 -5 7 5 -7 5" fill="none" stroke="#9CA3AF" stroke-width="1.5"/>${!hero && state.labels ? `<text x="${x + 39}" y="135" text-anchor="middle" fill="#6B7280" font-size="11">${port}</text>` : ""}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 300" role="img" aria-label="Пример сети: веб-сервер, сервер приложений и база данных" font-family="Arial, sans-serif">
    <rect x="18" y="26" width="744" height="250" rx="16" fill="#F9FAFF" stroke="#C7D2FE"/>
    <text x="40" y="53" fill="#6B7280" font-size="12">Пример сети</text>
    ${onlyHigh ? "" : arrow(224, "8080")}${arrow(478, "5432")}${nodes}
  </svg>`;
}
function home() {
  return `<section class="hero"><div><div class="eyebrow">СЕТЬ ПОНЯТНА. ДОКУМЕНТАЦИЯ ГОТОВА.</div><h1>Ваша архитектура.<br>На одной схеме.</h1><p>Превратите описание сети в наглядную документацию. Загрузите файл, выберите профиль и получите схему в PlantUML или PNG.</p><a class="btn" href="upload.html">Создать документацию <span>→</span></a></div><div class="hero-art">${diagram(true)}</div></section><div class="section-head"><h2>От файла к схеме — три шага</h2><span>Меньше рутины, больше ясности</span></div><div class="grid3">${[
    [
      "01",
      "Загрузите описание сети",
      "Добавьте файл YAML, JSON или CSV с данными о хостах, сервисах и соединениях.",
    ],
    [
      "02",
      "Выберите нужный ракурс",
      "Посмотрите на архитектуру по хостам, сервисам или уровню критичности.",
    ],
    [
      "03",
      "Сохраните результат",
      "Получите исходный PlantUML и изображение схемы для документации.",
    ],
  ]
    .map(
      (x) =>
        `<article class="card"><div class="stepnum">${x[0]}</div><h3>${x[1]}</h3><p>${x[2]}</p></article>`,
    )
    .join(
      "",
    )}</div><div class="strip"><div><h3>Сначала познакомимся?</h3><p>Откройте пример и пройдите весь путь без своего файла.</p></div><button class="btn secondary" onclick="useDemo()">Попробовать пример →</button></div>`;
}
function upload() {
  return (
    head(
      "ШАГ 01 / 03",
      "Загрузка файла",
      "Добавьте описание сети, для которой нужна документация.",
    ) +
    steps(1) +
    `<div class="twocol"><section class="card"><h2>Исходные данные</h2><p>Выберите файл с описанием вашей сети.</p><div class="drop" id="drop"><div class="upload-icon">↥</div><h3>Перетащите файл сюда</h3><p>или выберите его на компьютере</p><button class="btn" onclick="$('#fileinput').click()">Выбрать файл</button><span class="small" style="margin-top:13px">YAML, YML, JSON, CSV · до 10 МБ</span><input id="fileinput" type="file" accept=".yaml,.yml,.json,.csv" hidden></div><div id="fileinfo">${fileInfo()}</div><div class="note">Полная проверка структуры и генерация по вашему файлу будут подключены к серверным модулям команды.</div><div class="actions"><a class="small" href="index.html">← На главную</a><button class="btn" id="next" ${!state.file ? "disabled" : ""} onclick="go('settings')">Продолжить →</button></div></section><div><section class="card"><div class="tag">ПОДСКАЗКА</div><h2 style="margin-top:17px">Что должно быть в файле?</h2><ul class="list"><li><strong>Хосты</strong>Названия и адреса узлов сети.</li><li><strong>Сервисы</strong>Сервисы и их размещение на хостах.</li><li><strong>Соединения</strong>Связи, порты и уровень критичности.</li></ul></section><section class="card" style="margin-top:18px"><h3>Нет файла под рукой?</h3><p>Используйте небольшой учебный пример.</p><button class="btn secondary" style="margin-top:15px" onclick="download('network-example.json',JSON.stringify(example,null,2),'application/json')">↓ Скачать JSON</button><button class="btn" style="margin-top:10px" onclick="useDemo()">Открыть пример →</button></section></div></div>`
  );
}
function fileInfo() {
  return state.file
    ? `<div class="file"><div><strong style="font-size:12px">${escapeHTML(state.file.name)}</strong><br><span class="small">${state.demo ? "Демонстрационные данные" : Math.ceil(state.file.size / 1024) + " КБ · файл выбран"}</span></div><button aria-label="Удалить файл" style="background:transparent" onclick="state.file=null;state.demo=false;render()">✕</button></div>`
    : "";
}
async function generateFromServer() {
  try {
    const file = await getUploadedFile();

    if (!file) {
      toast("Файл не найден. Загрузите его ещё раз.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile", state.profile);

    toast("Генерация диаграммы...");

    const response = await fetch("/api/generate", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      toast(result.error || "Не удалось создать диаграмму.");
      return;
    }

    sessionStorage.setItem(
      "netforma-result",
      JSON.stringify(result)
    );

    state.generated = true;
    state.tab = "diagram";
    go("results");

  } catch (error) {
    console.error(error);
    toast("Не удалось связаться с сервером.");
  }
}
function settings() {
  return (
    head(
      "ШАГ 02 / 03",
      "Настройки схемы",
      "Выберите, как представить архитектуру вашей сети.",
    ) +
    steps(2) +
    `<div class="twocol"><section class="card"><h2>Профиль документации</h2><p>Один набор данных — три взгляда на архитектуру.</p>${[
      ["hosts", "По хостам", "Серверы, их адреса и связи между узлами."],
      ["services", "По сервисам", "Сервисы и зависимости между ними."],
      [
        "critical",
        "По критичности",
        "Акцент на значимых компонентах и связях.",
      ],
    ]
      .map(
        (x) =>
          `<label class="profile"><input type="radio" name="profile" value="${x[0]}" ${state.profile === x[0] ? "checked" : ""} onchange="state.profile=this.value;render()"><div><h3>${x[1]}</h3><p>${x[2]}</p></div></label>`,
      )
      .join(
        "",
      )}<div class="field"><label for="criticality">Уровень критичности</label><select id="criticality" onchange="state.criticality=this.value;saveState()"><option value="all" ${state.criticality === "all" ? "selected" : ""}>Все уровни</option><option value="high" ${state.criticality === "high" ? "selected" : ""}>Только высокий</option><option value="medium" ${state.criticality === "medium" ? "selected" : ""}>Средний и высокий</option></select></div><label class="check"><input type="checkbox" ${state.labels ? "checked" : ""} onchange="state.labels=this.checked;saveState()">Показывать подписи портов на связях</label></section><section class="card" style="align-self:start"><span class="tag">ПАРАМЕТРЫ ГЕНЕРАЦИИ</span><h2 style="margin-top:18px">Всё готово к запуску</h2><div class="summary"><span>Файл</span><b>${state.file ? escapeHTML(state.file.name) : "Не выбран"}</b></div><div class="summary"><span>Профиль</span><b>${profiles[state.profile]}</b></div><div class="summary"><span>Результат</span><b>PlantUML + PNG</b></div><button class="btn" style="width:100%;margin-top:22px" onclick="generateFromServer()">Сгенерировать диаграмму →</button><a href="upload.html" class="small" style="display:block;text-align:center;margin-top:16px">← Назад к файлу</a></section></div>`
  );
}
function puml() {
  const names =
    state.profile === "services"
      ? ["Nginx", "API", "PostgreSQL"]
      : ["Веб-сервер", "Сервер приложений", "База данных"];
  return (
    "@startuml\nleft to right direction\nskinparam backgroundColor #F7F8FC\nskinparam componentBackgroundColor #E0E7FF\n" +
    names.map((n, i) => `component "${n}" as n${i}`).join("\n") +
    "\n" +
    (state.criticality === "high"
      ? ""
      : `n0 --> n1${state.labels ? " : 8080" : ""}\n`) +
    `n1 --> n2${state.labels ? " : 5432" : ""}\n@enduml\n`
  );
}
function results() {
  const result = getServerResult();

  if (!result || !result.statistics) {
    return (
      head(
        "ШАГ 03 / 03",
        "Результаты генерации",
        "Сначала загрузите файл и запустите генерацию."
      ) + steps(3) +
      `<div class="notice">
        <div><b>Результаты не найдены</b><br>
        Вернитесь к настройкам и запустите генерацию.</div>
      </div>`
    );
  }

  const stats = result.statistics;

  const hostsCount = stats.hosts?.length || 0;
  const connectionsCount = stats.connections?.length || 0;

  return (
    head(
      "ШАГ 03 / 03",
      "Результаты генерации",
      "Просмотрите схему и сохраните файлы документации.",
      '<a class="btn secondary" href="upload.html">+ Новый файл</a>'
    ) +
    steps(3) +
    `<div class="notice">
      <div><b>Файл успешно обработан</b><br>
      Схема создана серверными модулями.</div>
    </div>
    <div class="metrics">
      <div class="metric"><span>Хосты</span><strong>${hostsCount}</strong></div>
      <div class="metric"><span>Сервисы</span><strong>—</strong></div>
      <div class="metric"><span>Соединения</span><strong>${connectionsCount}</strong></div>
    </div>
    <div class="workspace">
      <div class="toolbar">
        <div class="tabs">
          <button class="${state.tab === "diagram" ? "active" : ""}"
            onclick="state.tab='diagram';render()">Схема сети</button>
          <button class="${state.tab === "code" ? "active" : ""}"
            onclick="state.tab='code';render()">Код PlantUML</button>
        </div>
        <span class="tag">${profiles[state.profile]}</span>
      </div>
      <div class="diagram">
        ${
          state.tab === "diagram"
            ? `<img src="${result.png_url}" alt="Схема сети" style="width:100%;height:auto;">`
            : `<a href="${result.puml_url}" target="_blank">Открыть исходный код PlantUML</a>`
        }
      </div>
    </div>
    <div class="actions">
      <a class="btn secondary" href="settings.html">← Изменить настройки</a>
      <div style="display:flex;gap:10px">
        <a class="btn secondary" href="${result.puml_url}" download>↓ PlantUML</a>
        <a class="btn" href="${result.png_url}" download>↓ Скачать PNG</a>
      </div>
    </div>`
  );
}
function resultDiagram() {
  return diagram();
}
function escapeHTML(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
}
function useDemo() {
  state.file = {
    name: "network-example.json",
    size: JSON.stringify(example).length,
  };
  state.demo = true;
  go("settings");
}
const FILE_DB_NAME = "netforma-files";
const FILE_STORE_NAME = "uploads";

function openFileDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(FILE_DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;

      if (!db.objectStoreNames.contains(FILE_STORE_NAME)) {
        db.createObjectStore(FILE_STORE_NAME);
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function saveUploadedFile(file) {
  const db = await openFileDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(FILE_STORE_NAME, "readwrite");

    transaction.objectStore(FILE_STORE_NAME).put(file, "network-file");

    transaction.oncomplete = () => {
      db.close();
      resolve();
    };

    transaction.onerror = () => {
      db.close();
      reject(transaction.error);
    };

    transaction.onabort = () => {
      db.close();
      reject(transaction.error);
    };
  });
}

async function getUploadedFile() {
  const db = await openFileDB();

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(FILE_STORE_NAME, "readonly");
    const request = transaction
      .objectStore(FILE_STORE_NAME)
      .get("network-file");

    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);

    transaction.oncomplete = () => db.close();
    transaction.onerror = () => db.close();
  });
}
async function choose(file) {
  if (!file) return;
  if (!/\.(yaml|yml|json|csv)$/i.test(file.name)) {
    toast("Выберите файл YAML, JSON или CSV.");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    toast("Размер файла превышает 10 МБ.");
    return;
  }
  if (!file.size) {
    toast("Файл пуст. Выберите другой файл.");
    return;
  }
  if (/\.json$/i.test(file.name)) {
    try {
      JSON.parse(await file.text());
    } catch {
      toast("В JSON есть синтаксическая ошибка. Проверьте файл.");
      return;
    }
  }
try {
  await saveUploadedFile(file);
} catch (error) {
  toast("Не удалось сохранить файл в браузере.");
  return;
}

state.file = { name: file.name, size: file.size };
state.demo = false;
saveState();
render();
}
function render() {
  let page = document.body.dataset.page || "home";
  if (!titles[page]) page = "home";
  $("#crumb").textContent = titles[page];
  document
    .querySelectorAll("nav a")
    .forEach((a) => a.classList.toggle("active", a.dataset.page === page));
  $("#content").innerHTML = { home, upload, settings, results }[page]();
  if (page === "upload") {
    $("#fileinput").onchange = (e) => choose(e.target.files[0]);
    const d = $("#drop");
    d.ondragover = (e) => {
      e.preventDefault();
      d.classList.add("drag");
    };
    d.ondragleave = () => d.classList.remove("drag");
    d.ondrop = (e) => {
      e.preventDefault();
      choose(e.dataTransfer.files[0]);
    };
  }
}
function savePNG() {
  const img = new Image();
  const url = URL.createObjectURL(
    new Blob([resultDiagram()], { type: "image/svg+xml" }),
  );
  img.onload = () => {
    const c = document.createElement("canvas");
    c.width = 1560;
    c.height = 600;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#f7f8fc";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.drawImage(img, 0, 0, c.width, c.height);
    c.toBlob((b) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(b);
      a.download = "network-example.png";
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    });
    URL.revokeObjectURL(url);
  };
  img.onerror = () => toast("Не удалось сохранить изображение.");
  img.src = url;
}
window.addEventListener("pagehide", saveState);
render();
