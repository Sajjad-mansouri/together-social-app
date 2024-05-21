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

function addPost() {
    const btn = document.querySelector('.add-button')
    console.log('add function')
    formModal(btn)
    const form = document.querySelector('.add-form form')

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        console.log(formData)
        getToken().then((accessToken) => {
            fetch('http://localhost:8000/api/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`
                    },
                    body: formData
                })
                .then((resp) => {
                    if (resp.ok) {
                        return resp.json()

                    }
                })
                .then((data) => {
                    const modal = document.querySelector('.add-form')
                    modal.style.display = 'none';
                    form.reset();
                    const content = document.querySelector('.content');
                    const postTemplate = document.querySelector('.card');
                    let cloned = postTemplate.cloneNode(true);
                    cloned.classList.remove('hidden');
                    const title = cloned.querySelector('.post-title');
                    const text = cloned.querySelector('.post-text');
                    const img = cloned.querySelector('img');
                    const postCreated = cloned.querySelector('.post-created');

                    img.src = data.image;
                    title.textContent = data.title;
                    text.textContent = data.text;
                    postCreated.textContent = 'now'

                    content.prepend(cloned);
                })
        })


    })

}




const loginForm = document.querySelector('.login')
if (loginForm) {
    console.log('loginform')

    loginForm.addEventListener('submit', (event) => login(event))
}

function search(btn) {


    searchInput.addEventListener('input', (event) => {

        const search = event.target.value.trim();

        if (event.target.value.trim() != "") {
            getToken().then((accessToken) => {
                fetch(`http://localhost:8000/api/users/?search=${event.target.value.trim()}`, {
                        method: "GET",
                        headers: {
                            Authorization: `Bearer ${accessToken}`
                        }
                    })
                    .then((response) => {
                        if (response.ok) {
                            return response.json()
                        }
                    })
                    .then((data) => {

                        searchCard.classList.remove('hidden')
                        searchCard.textContent = ''
                        const ul = document.createElement('ul');
                        if (data.length >= 1) {

                            data.forEach((user) => {
                                const li = document.createElement('li');
                                const link = document.createElement('a')
                                link.setAttribute('href', baseUrl + '/profile/' + user.username)
                                link.textContent = user.username;
                                li.append(link);
                                ul.append(li);
                                console.log('this is')
                            })
                        } else {
                            const li = document.createElement('li');
                            li.textContent = 'no user found';
                            ul.append(li)
                        }
                        searchCard.append(ul);
                        console.log(searchCard)

                    })
            })

        } else {
            searchCard.classList.add('hidden');
        }
    })


}


async function follow(btn) {
    const accessToken = await getToken()

    const type = btn.getAttribute('data-type');
    const toUser = btn.getAttribute('data-owner');
    const contact = btn.getAttribute('data-contact')
    const body = { 'to_user': toUser }
    if (type === 'follow') {

        const jsBody = JSON.stringify(body)
        const response = await fetch('http://localhost:8000/api/contact/', {
            method: 'POST',
            headers: {
                "Authorization": `Bearer ${accessToken}`,
                "Content-Type": "application/json",
            },
            body: jsBody
        })
        if (response.ok) {
            const data = await response.json()
            btn.setAttribute('data-contact', data.id)
            btn.textContent = 'UnFollow'
            btn.setAttribute('data-type', 'unfollow')
        }

    } else if (type === 'unfollow') {
        const response = await fetch(`http://localhost:8000/api/contact/${contact}`, {
            method: 'Delete',
            headers: {
                Authorization: `Bearer ${accessToken}`
            }

        })
        if (response.ok) {

            btn.setAttribute('data-contact', '')
            btn.setAttribute('data-type', 'follow')
            btn.textContent = 'Follow'
        }
    }

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