import { getToken, login } from './get-token.js'

let loginForm = document.querySelector('.login form')
console.log(loginForm)
loginForm.addEventListener('submit', (event) => {
    login(event)
})


class TextType {
    constructor() {
        this.texts = ["Hi, Im Sajjad Mansouri.", "Welcome to my site!", "I Love Design.", "I Love to Develop."]
        this.wordIndex = 0
        this.sentenceIndex = 0
        this.isDeleting = false

        this.span = document.querySelector('.wrap')

    }

    typing() {

        let text = this.texts[this.sentenceIndex]
        this.delta = 100 - Math.random() * 100;
        if (this.isDeleting) {
            this.delta /= 2
            this.wordIndex -= 1
        } else {

            this.wordIndex += 1
        }
        this.span.textContent = text.substring(-1, this.wordIndex + 1)

        if (this.wordIndex == text.length - 1) {
            this.isDeleting = true
            this.delta = 2000
        }
        if (this.wordIndex == -1) {
            this.isDeleting = false
            this.delta = 500
            if (this.sentenceIndex == this.texts.length - 1) {
                this.sentenceIndex = 0
            } else {
                this.sentenceIndex += 1
            }

        }

        setTimeout(() => this.typing(), this.delta)
    }


}


window.onload = function() {
    var elements = document.getElementsByClassName('typewrite');
    if(window.screen.width>498){
        
    for (var i = 0; i < elements.length; i++) {


        let type = new TextType();
        type.typing()

    }
    // INJECT CSS
    var css = document.createElement("style");
    }
    css.type = "text/css";
    css.innerHTML = ".typewrite > .wrap { border-right: 0.08em solid #fff}";
    document.body.appendChild(css);
};