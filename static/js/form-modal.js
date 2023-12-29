import { getToken, login } from './get-token.js'

// const modal = document.querySelector('.add-form');
const searchInput = document.getElementById('search-input')
const searchCard = document.querySelector('.search-card')

function formModal() {
    document.querySelectorAll('button.btn-modal').forEach(btn => {
        const data = btn.getAttribute('data-modal');
        const modal = document.querySelector(`[data-modal="${data}"]`)
        console.log(modal)
        btn.addEventListener('click', () => {
            console.log('add')
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
    });


}

function addPost() {
    const form = document.querySelector('.add-form form')

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

                        searchCard.classList.remove('hidden')
                        searchCard.textContent = ''
                        const ul = document.createElement('ul');
                        if (data.length >= 1) {

                            data.forEach((user) => {
                                const li = document.createElement('li');
                                const link = document.createElement('a')
                                link.setAttribute('href', user.username)
                                link.textContent = user.username;
                                li.append(link);
                                ul.append(li);
                            })
                        } else {
                            const li = document.createElement('li');
                            li.textContent = 'no user found';
                            ul.append(li)
                        }
                        searchCard.append(ul);

                    })
            })

        } else {
            searchCard.classList.add('hidden');
        }

    })
}

if (searchInput) {
    search();
    document.addEventListener('mouseup', (event) => {
        if (!event.target.closest('.card')) {
            searchCard.classList.add('hidden');
        }
    })
}


async function follow(btn) {
    const accessToken = await getToken()

    const type = btn.getAttribute('data-type');
    const toUser = btn.getAttribute('data-owner');
    const contact=btn.getAttribute('data-contact')
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
        if (response.ok){
        	const data=await response.json()
        	btn.setAttribute('data-contact',data.id)
        	btn.textContent='UnFollow'
        	btn.setAttribute('data-type','unfollow')
        }
        
    } else if (type === 'unfollow') {
        const response = await fetch(`http://localhost:8000/api/contact/${contact}`, {
            method: 'Delete',
            headers: {
                Authorization: `Bearer ${accessToken}`
            }

        })
       	if (response.ok){
       		
       		btn.setAttribute('data-contact','')
       		btn.setAttribute('data-type','follow')
       		btn.textContent='Follow'
       	}
    }

}

const followBtns = document.querySelectorAll('.follow-btn')
if (followBtns) {

    followBtns.forEach(btn => {
        btn.addEventListener('click', ()=>follow(btn))
    })
}