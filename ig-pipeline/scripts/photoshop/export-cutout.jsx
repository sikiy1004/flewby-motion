// Photoshop: export the ACTIVE document (after you refined the mask by hand, e.g. Select and Mask)
// as a trimmed transparent PNG to assets/products/manual/<product-id>.png.
// Layer masks on the active layer are applied; the document itself is not modified.
#target photoshop
(function () {
  if (!app.documents.length) { alert("ドキュメントが開かれていません"); return; }
  var root = File($.fileName).parent.parent.parent;
  var outDir = Folder(root.fsName + "/assets/products/manual");
  if (!outDir.exists) outDir.create();
  var src = app.activeDocument;
  var id = prompt("商品ID（data/products.json の id）", decodeURI(src.name).replace(/\.[^.]+$/, ""));
  if (!id) return;
  var doc = src.duplicate(id, true); // merged copy
  try {
    doc.trim(TrimType.TRANSPARENT, true, true, true, true);
    doc.resizeCanvas(UnitValue(doc.width.as("px") + 32, "px"), UnitValue(doc.height.as("px") + 32, "px"), AnchorPosition.MIDDLECENTER);
    doc.saveAs(File(outDir.fsName + "/" + id + ".png"), new PNGSaveOptions(), true, Extension.LOWERCASE);
    alert("保存しました → assets/products/manual/" + id + ".png");
  } finally {
    doc.close(SaveOptions.DONOTSAVECHANGES);
  }
})();
