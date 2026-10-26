() => {
  // note の記事ページから、公開されている情報だけを取り出す（browser_evaluate の function にこの全文を渡す）。
  // 有料部分は購入しない限り表示されないので、取れるのは無料部分まで。
  // セレクタは note 側の変更で壊れうるため、JSON-LD → meta → DOM の順に試し、どこから取れたかを source に残す。
  const text = (el) => (el ? el.innerText.replace(/\n{3,}/g, "\n\n").trim() : "");
  const meta = (name) =>
    document.querySelector(`meta[property="${name}"], meta[name="${name}"]`)?.getAttribute("content") || "";

  let ld = {};
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const data = [].concat(JSON.parse(s.textContent));
      const article = data.find((d) => /Article|BlogPosting/.test(String(d["@type"])));
      if (article) { ld = article; break; }
    } catch (e) { /* 壊れた JSON-LD は無視する */ }
  }

  const bodyEl =
    document.querySelector('[data-name="body"]') ||
    document.querySelector(".note-common-styles__textnote-body") ||
    document.querySelector("article") ||
    document.querySelector("main");
  const body = text(bodyEl);
  const page = document.body ? document.body.innerText : "";
  const price = page.match(/[￥¥]\s?([0-9,]+)/);
  const author = typeof ld.author === "object" ? [].concat(ld.author)[0]?.name : ld.author;

  return {
    url: location.href,
    fetched_at: new Date().toISOString(),
    title: ld.headline || meta("og:title") || text(document.querySelector("h1")) || document.title,
    author: author || meta("author") || meta("twitter:creator") || "",
    published_at: ld.datePublished || document.querySelector("time[datetime]")?.getAttribute("datetime") || "",
    description: meta("og:description") || meta("description"),
    // 価格と有料判定はページの文言からの推定。初回の実地テストで当たり外れを確認すること
    price_hint: price ? price[1].replace(/,/g, "") : "",
    paywall_hint: /この続きをみるには|この記事は有料|購入すると/.test(page),
    hashtags: [...document.querySelectorAll('a[href*="/hashtag/"]')].map((a) => a.innerText.trim()).filter(Boolean),
    body,
    body_chars: body.replace(/\s/g, "").length,
    source: { title: ld.headline ? "json-ld" : meta("og:title") ? "og" : "dom", body: bodyEl ? bodyEl.tagName.toLowerCase() + (bodyEl.className ? "." + String(bodyEl.className).split(" ")[0] : "") : "none" },
    login_hint: !!document.querySelector('a[href*="/login"]') ? "login_link_visible" : "no_login_link",
  };
}
