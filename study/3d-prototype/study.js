"use strict";

// Both conditions start from the same checked prefix. The unmodified Explorer
// owns the journal, state, accessible evidence table, and exact event detail.
const studyPrefix = Number(document.body.dataset.studyPrefix);
const studySlider = document.getElementById("prefix-slider");
if (Number.isInteger(studyPrefix) && studyPrefix >= 0 && studyPrefix <= Number(studySlider.max)) {
  studySlider.value = String(studyPrefix);
  studySlider.dispatchEvent(new Event("input", {bubbles: true}));
}
