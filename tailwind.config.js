module.exports = {
  content: [
    "./main/templates/**/*.html",
    "./main/static/src/**/*.js"
  ],
  plugins: [
    require("daisyui"),
    require("@tailwindcss/typography")
  ],
  daisyui: {
    themes: ["fantasy2,synthwave2"],
  }
}