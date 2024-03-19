import { getToken, login } from './get-token.js'
import {imageUpload,changeProfile} from './profile.js'

// add post modal and send post to api
if(window.location.pathname==='/home/'){
const post=document.querySelector('.add-post')
post.addEventListener('click',()=>{
    formModal(post)
    addPost()

})
}
function formModal(){
    const modal=document.querySelector('.add-form')
    modal.classList.remove('hidden')

    window.addEventListener('mouseup',(e)=>{
        if (!event.target.closest('.form-modal')){
            modal.classList.add('hidden')
            modal.querySelectorAll('input').forEach(input=>{
                input.value='';
            })
        }
    })

}

function addPost() {
    const form = document.querySelector('.add-form form')

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(form);
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
                    console.log(data)
                    const modal = document.querySelector('.add-form')
                    modal.style.display = 'none';
                    form.reset();
                    const postContainer = document.querySelector('.post-container');
                    const postTemplate = document.querySelector('.post-card');
                    let cloned = postTemplate.cloneNode(true);
                    cloned.classList.remove('hidden');
                
                    const text = cloned.querySelector('.content .description');
                    const img = cloned.querySelector('.content img');
                    const postCreated = cloned.querySelector('.post-created');
                    const ownerImage=cloned.querySelector('.post-owner img')
                    const ownerUsername=cloned.querySelector('.post-owner span')
                    const likeDiv=cloned.querySelector('.like')
                    likeDiv.setAttribute('data-post',data.id)
                    likeDiv.addEventListener('click',()=>{
                        like(likeDiv)
                    })

                    img.src = data.image;
                    text.textContent = data.text;
                    ownerImage.src=data.owner.profile_image
                    ownerUsername.textContent=data.owner.username
                    postCreated.textContent = 'now'

                    postContainer.prepend(cloned);
                })
        })


    })

}


// search user
const searchInput = document.getElementById('search-input')
if (window.location.pathname==='/search/'){
    search()
}

function search() {


    searchInput.addEventListener('input', (event) => {

        const search = event.target.value.trim();
        const searchResult=document.querySelector('.search-result');

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
                        console.log(data)
                        
                        searchResult.classList.remove('hidden');
                        searchResult.textContent='';
                        if (data.length >= 1) {
                        data.forEach(user=>{
                            const result=document.createElement('div');
                            result.classList.add('search-user');
                            result.textContent=user.username;
                            searchResult.append(result)
                        })
                            }else{
                                searchResult.textContent='no result found'
                            }
                    })
            })

        } else {
            searchResult.classList.add('hidden');
        }
    })


}


// follow and unfollow user
if (window.location.pathname==='/profile/'){
    const connect=document.querySelector('.connect');
    connect.addEventListener('click',()=>follow(connect))
    
}

async function follow(btn) {
    console.log(btn)
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

// like and unlike post

document.querySelectorAll('.like').forEach(div=>{
    div.addEventListener('click',()=>{
        like(div)
    })
})
async function like(div) {

    const dataType = div.getAttribute('data-type');

    const dataPost = div.getAttribute('data-post');
    const dataLike = div.getAttribute('data-like');

    const accessToken = await getToken()

    console.log(dataPost)
    if (dataType === 'True') {
        const response = await fetch(origin + `/api/like/${dataLike}`, {
            method: "DELETE",
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })
        if (response.ok) {

            const likeIcon = div.querySelector('.fa-heart')
            const likeCount = div.parentNode.nextElementSibling;

            likeIcon.style.color = 'black'
            div.setAttribute('data-type', 'False')
            likeCount.textContent = Number(likeCount.textContent) - 1
        }

    } else if (dataType === 'False') {

        const body = { 'post': dataPost }

        const response = await fetch(origin + '/api/like/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        })


        if (response.ok) {
            const data = await response.json()

            const likeIcon = div.querySelector('.fa-heart')
            const likeCount = div.parentNode.nextElementSibling;
            likeIcon.style.color = 'red';
            div.setAttribute('data-type', 'True')
            div.setAttribute('data-like', data.id)
            likeCount.textContent = Number(likeCount.textContent) + 1
        }

    }
}