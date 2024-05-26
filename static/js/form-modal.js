import { getToken, login } from './get-token.js'
import { imageUpload, changeProfile } from './profile.js'

// const modal = document.querySelector('.add-form');
const searchInput = document.getElementById('search-input')
const searchCard = document.querySelector('.search-card')

const baseUrl = window.location.origin

function formModal(btn) {
    console.log(btn)
    const data = btn.getAttribute('data-type');
    const modal = document.querySelector(`div[data-modal="${data}"]`)
    console.log(modal)
    btn.addEventListener('click', () => {
        console.log('toggle add')
        modal.classList.toggle('hidden');
    })
    window.addEventListener('mouseup', (event) => {
        if (!event.target.closest('.form-modal') && !event.target.closest('.btn-modal')) {
            modal.classList.add('hidden');
            modal.querySelectorAll('input').forEach(input => {
                input.value = '';
            })
        }
    })



}






const loginForm = document.querySelector('.login')
if (loginForm) {
    console.log('loginform')

    loginForm.addEventListener('submit', (event) => login(event))
}





document.querySelectorAll('.btn').forEach(btn => {
    const dataType = btn.getAttribute('data-type')
    if (dataType == 'follow' || dataType == 'unfollow') {
        btn.addEventListener('click', () => follow(btn))
    } else if (dataType == 'add') {


        addPost()


    } else if (dataType == 'search') {
        formModal(btn)
        btn.addEventListener('click', () => search(btn))
    } else if (dataType == 'home') {
        btn.addEventListener('click', () => {

            window.location.pathname = 'home'
        })
    } else if (dataType == 'profile') {
        btn.addEventListener('click', () => {
            window.location.pathname = 'profile'
        })
    } else if (dataType == 'logout') {
        btn.addEventListener('click', () => {

            const logout = document.querySelector('.logout');
            logout.submit()
        })
    } else if (dataType == 'info') {
        btn.addEventListener('click', () => {
            window.location.pathname = 'account/profile'
        })
    } else if (dataType == 'profile-image') {
        btn.addEventListener('click', () => {
            console.log('profile')
            imageUpload(btn);
        })
    } else if (dataType == 'submit') {
        btn.addEventListener('click', (event) => {
            event.preventDefault();
            const profileForm = document.querySelector('#user-form')
            const formData = new FormData(profileForm);
            const email = document.querySelector('#email').getAttribute('data-current');
            const username = document.querySelector('#username').getAttribute('data-current');
            if (formData.get('email') === email) {
                formData.delete('email')
            }
            if (formData.get('username') === username) {
                formData.delete('username')
            }

            const formDataObject = Object.fromEntries(formData.entries());
            const userFormData = { 'user': formDataObject }
            const userJsonFormData = JSON.stringify(userFormData);
            changeProfile(userJsonFormData)

        })
    } else if (dataType == 'liked-post') {
        btn.addEventListener('click', () => {
            console.log(window.location)
            window.location.href = origin + '/liked-post'
        })
    }

})








// console.log(window.location.pathname)
// if (window.location.pathname === '/profile/') {
//     const menu = document.querySelector('.menu');
//     menu.addEventListener('click', () => {
//         const div = menu.querySelector('div');
//         div.classList.toggle('hidden')
//     })
// }