// Photoshop: batch "Remove Background" → apply mask → trim → PNG into assets/products/manual/
// Use when rembg is not good enough (white-on-white, hair-thin cables, chrome reflections).
// Run:  File > Scripts > Browse… (this file)   or   bash scripts/photoshop/run.sh remove-bg
// The file name (without extension) must be the product id, e.g. raw/hair-dryer.jpg → manual/hair-dryer.png
#target photoshop
(function () {
  var root = File($.fileName).parent.parent.parent; // ig-pipeline/
  var rawDir = Folder(root.fsName + "/assets/products/raw");
  var outDir = Folder(root.fsName + "/assets/products/manual");
  if (!outDir.exists) outDir.create();

  var files = File.openDialog("切り抜く商品画像を選択（複数可）", function (f) { return f instanceof Folder || /\.(jpe?g|png|tiff?|webp|psd)$/i.test(f.name); }, true);
  if (!files) return;
  if (!(files instanceof Array)) files = [files];
  var prevUnits = app.preferences.rulerUnits;
  app.preferences.rulerUnits = Units.PIXELS;
  var done = [];
  for (var i = 0; i < files.length; i++) {
    var doc = app.open(files[i]);
    try {
      if (doc.activeLayer.isBackgroundLayer) doc.activeLayer.isBackgroundLayer = false;
      executeAction(stringIDToTypeID("removeBackground"), undefined, DialogModes.NO); // Quick Action (adds a layer mask)
      applyMask();
      doc.trim(TrimType.TRANSPARENT, true, true, true, true);
      doc.resizeCanvas(doc.width + 32, doc.height + 32, AnchorPosition.MIDDLECENTER); // 16 px padding like rembg output
      var id = decodeURI(doc.name).replace(/\.[^.]+$/, "");
      doc.saveAs(File(outDir.fsName + "/" + id + ".png"), new PNGSaveOptions(), true, Extension.LOWERCASE);
      done.push(id);
    } catch (e) {
      alert(files[i].name + ": " + e);
    }
    doc.close(SaveOptions.DONOTSAVECHANGES);
  }
  app.preferences.rulerUnits = prevUnits;
  alert("書き出し完了: " + done.join(", ") + "\n→ assets/products/manual/\n細部は export-cutout.jsx で手直しできます。");

  function applyMask() {
    var d = new ActionDescriptor(), r = new ActionReference();
    r.putEnumerated(charIDToTypeID("Chnl"), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
    d.putReference(charIDToTypeID("null"), r);
    d.putBoolean(charIDToTypeID("Aply"), true);
    executeAction(charIDToTypeID("Dlt "), d, DialogModes.NO);
  }
})();
