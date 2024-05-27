import { getToken, login } from './get-token.js'

let loginForm=document.querySelector('.login form')
console.log(loginForm)
loginForm.addEventListener('submit',(event)=>{
    login(event)
})