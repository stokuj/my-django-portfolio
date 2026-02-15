module.exports = {
  content: [
    "./django/main/templates/**/*.html",
    "./django/main/static/src/**/*.js"
  ],
  plugins: [
    require("daisyui"),
    require("@tailwindcss/typography")
  ]
}
