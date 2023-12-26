import { getToken, login } from './get-token.js'

const modal = document.querySelector('.add-form');
const searchInput = document.getElementById('search-input')
const divCard = document.querySelector('.card')

function formModal() {
    const addButton = document.querySelector('.add-button');
    addButton.addEventListener('click', () => {

        modal.classList.toggle('hidden');
        window.addEventListener('mouseup', (event) => {
            if (!event.target.closest('.add-form') && !event.target.closest('.add-button')) {
                modal.classList.add('hidden');
            }
        })
    })

}

function addPost() {
    const formDiv = document.querySelector('.add-form');
    const form = formDiv.querySelector('form')
    console.log(form)
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        console.log(formData)
        getToken().then((accessToken) => {
            console.log(accessToken)
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
                    console.log(data);
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
                    console.log(postCreated);
                    img.src = data.image;
                    title.textContent = data.title;
                    text.textContent = data.text;
                    postCreated.textContent = 'now'

                    content.prepend(cloned);
                })
        })


    })

}


if (window.location.pathname === '/profile/') {
    formModal()
    addPost()
}

const loginForm = document.querySelector('.login')
if (loginForm) {
    console.log('loginform')

    loginForm.addEventListener('submit', (event) => login(event))
}

function search() {
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

                        divCard.classList.remove('hidden')
                        divCard.textContent = ''
                        const ul = document.createElement('ul');
                        if (data.length>=1){

                        data.forEach((user) => {
                            const li = document.createElement('li');
                            li.textContent = user.username;
                            ul.append(li);
                        })
                    }else{
                    	const li = document.createElement('li');
                    	li.textContent='no user found';
                    	ul.append(li)
                    }
                        divCard.append(ul);

                    })
            })

        }else{
        	divCard.classList.add('hidden');
        }

    })
}

if (searchInput) {
    search();
    document.addEventListener('mouseup', (event) => {
        if (!event.target.closest('.card')) {
            divCard.classList.add('hidden');
        }
    })
}