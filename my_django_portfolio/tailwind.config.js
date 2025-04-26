module.exports = {
  content: [
    "./personal_portfolio/main/templates/**/*.html",
    "./personal_portfolio/main/static/src/**/*.js"
  ],
  plugins: [
    require("daisyui"),
    require("@tailwindcss/typography")
  ],
  daisyui: {
    themes: ["light"],
  }
}