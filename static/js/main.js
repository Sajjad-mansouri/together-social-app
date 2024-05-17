import { getToken, login } from './get-token.js'
import { addEventListeners } from './form-modal.js'
/***************Post**************************/
const posts = document.querySelector(".posts");




/**************************video**************************/

/**************************search+notif-section **************************/
//search section notif
let search = document.getElementById("search");
let search_icon = document.getElementById("search_icon");
search_icon.addEventListener("click", function() {
    search.classList.toggle("show");
});

let notification = document.getElementById("notification");
let notification_icon = document.querySelectorAll(".notification_icon");
notification_icon.forEach((notif) => {
    notif.addEventListener('click', function() {
        notification.classList.toggle("show");
    })
})


/**************************icons+text change **************************/
//change the icon when the user click on it

//love btn


//save btn
let save_icon = document.querySelectorAll(".save");
save_icon.forEach(function(save) {
    save.addEventListener("click", function() {
        let not_save = save.children[1];
        let saved = save.children[0];
        not_save.classList.toggle("hide");
        saved.classList.toggle("hide");

    })
})

//notification follow 
let not_follow = document.querySelectorAll("#notification .notif.follow_notif")
not_follow.forEach(item => {
    let follow = item.children[0].children[1].children[0];
    follow.addEventListener("click", function(e) {
        e.stopPropagation();
        follow.classList.toggle("following");
        if (follow.classList.contains("following")) {
            follow.innerHTML = "Following";
            follow.style.backgroundColor = 'rgb(142, 142, 142)';
            follow.style.color = "black";
        } else {
            follow.innerHTML = "Follow";
            follow.style.backgroundColor = 'rgb(0, 149, 246)';
            follow.style.color = "white";
        }

    });
})

/**************************comments **************************/

//comments

function hideShowReply() {

    let show_replay = document.querySelectorAll(".comments .see_comment");

    show_replay.forEach(element => {
        let comments = element.closest('.comments');

        let hide_com = element.querySelector(" .see_comment .hide_com");
        let show_com = element.querySelector(" .see_comment .show_c");
        let replay_com = comments.querySelectorAll(" .responses");
        let replyCount = show_com.children[1]
        replyCount.textContent = replay_com.length;

        if (replay_com.length == 0) {

            element.remove()
        } else {

            element.addEventListener("click", function() {
                replay_com.forEach(item => {

                    item.classList.toggle('hide')
                })
                console.log(show_com)
                show_com.classList.toggle("hide");
                hide_com.classList.toggle("hide");
            });
        }
    })

}

function hideModal(cloneModal) {

    window.addEventListener('mouseup', event => {
        let modal = event.target.closest('.modal');
        let closeBtn;
        if (modal != null) {
            closeBtn = modal.querySelector('.btn-close');

        }

        if (event.target == closeBtn || !event.target.closest('.modal-content') && modal != null) {
            let modalBack = document.querySelector('.modal-backdrop')
            modalBack.remove();
            modal.remove();

        }
    })
}

function createCommentElement(modalBody, commentsSection, item) {

    if (item.main_comment == null) {
        let comment = commentsSection.cloneNode(true)
        comment.className = 'comments'
        comment.setAttribute('data-comment', item.id)
        let content = comment.querySelector('.content')
        let time = content.querySelector('span');
        let userName = content.querySelector('h4');
        let image = comment.querySelector('.comment img')
        let contentText = content.querySelector('p');
        contentText.textContent = item.comment;
        time.textContent = item.created;
        userName.textContent = item.author.username;
        image.src = item.author.profile.profile_image
        modalBody.append(comment)
    } else {
        //reply 
        //find comment that reply to that
        let comment = modalBody.querySelector(`.comments[data-comment="${item.main_comment}"]`)

        let responsesClone = comment.querySelector('.responses-clone');
        let response = responsesClone.cloneNode(true)
        response.className = 'responses hide'
        response.setAttribute('data-comment',item.id)
        let image = response.querySelector('img')
        image.src = item.author.profile.profile_image
        let content = response.querySelector('.content')
        let userName = content.querySelector('h4');
        let time = content.querySelector('span');
        userName.textContent = item.author.username;
        time.textContent = item.created;
        let replyText = content.querySelector('p');
        replyText.textContent = item.comment
        comment.append(response)


    }
}

let messageButtons = document.querySelectorAll('.chat button');
async function getComments(modalClone, postId) {
    let modalBody = modalClone.querySelector('.modal-body')
    let commentsSection = modalBody.querySelector('.comments-clone')
    let commentSection = commentsSection.querySelector('.comment')
    const accessToken = await getToken()

    const response = await fetch(`http://localhost:8000/api/post/${postId}/comments`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        },

    })
    const data = await response.json()

    if (response.ok) {
        if (data.length > 0) {

            data.forEach(item => {

                //comment not reply to comment
                //clone comments and use that
                createCommentElement(modalBody, commentsSection, item)
            })
        } else {
            modalBody.textContent = 'No comments yet!'
        }
        hideShowReply()
    }
}
messageButtons.forEach(element => {
    element.addEventListener('click', () => {
        let post = element.closest('.post')
        let postId = post.getAttribute('data-post');
        let modal = document.querySelector('#message_modal_clone')
        let modalBack = document.createElement('div')
        modalBack.className = 'modal-backdrop fade show'
        document.body.appendChild(modalBack)
        let modalClone = modal.cloneNode(true)
        modalClone.id = 'message_modal'
        getComments(modalClone, postId)
        modal.parentNode.insertBefore(modalClone, modal)
        modalClone.classList.add('show');
        modalClone.style.display = 'block';

        let input = modalClone.querySelector('.modal-footer input');
        console.log(input)
        writeComment(input, postId)

    })
})

hideModal()

//write comment


async function postComment(postId, comment) {
    let formData = new FormData()
    formData.append('comment', comment)

    formData.append('object_id', postId)
    const accessToken = await getToken()

    const response = await fetch(`http://localhost:8000/api/post/${postId}/comments`, {

        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(Object.fromEntries(formData))
    })
    const item = await response.json()
    if (response.ok) {
        let modalBody = document.querySelector('#message_modal .modal-body');
        console.log(modalBody)
        let commentSection = modalBody.querySelector('.comments-clone')
        createCommentElement(modalBody,commentSection,item)
    }
}

function writeComment(input, postId) {
    let form = input.closest('form')


    form.addEventListener('submit', (event) => {
        event.preventDefault()
        let inputValue = input.value;
        postComment(postId, inputValue)
    })



}

//delete comment
function deleteComment() {
    document.querySelector('.comments')
}
/**********Upload post*************/
const form = document.getElementById('upload-form');
const img_container = document.querySelector("#image-container");

form.addEventListener('change', handleSubmit);

let img_url;
//add the image post
function handleSubmit(event) {
    event.preventDefault();
    const img_container = document.querySelector("#image-container");
    const imageFile = document.getElementById('image-upload').files[0];
    const imageURL = URL.createObjectURL(imageFile);

    img_url = imageURL;
    handleNext(imageFile)
}

/////button submit


//add a description + click btn to share post
function handleNext(imageFile) {

    const image_description = document.querySelector("#image_description");

    if (image_description.classList.contains('hide_img')) {
        const next_btn_post = document.querySelector(".next_btn_post");
        const title_create = document.querySelector(".title_create");

        const modal_dialog = document.querySelector("#create_modal .modal-dialog");
        modal_dialog.classList.add("modal_share");
        image_description.classList.remove('hide_img')
        const image = document.createElement('img');
        image.src = img_url;
        const img_p = document.querySelector('.img_p');
        img_p.appendChild(image);
        next_btn_post.classList.add("share_btn_post");
        next_btn_post.classList.remove("next_btn_post");
        next_btn_post.innerHTML = 'Share';
        title_create.innerHTML = 'Create new post';
        completed(imageFile);
    }
}

function addPostHome(data) {
    let post = document.querySelector('.post');
    let postClone = post.cloneNode(true);
    let image = postClone.querySelector('.image img');
    let personInfo = postClone.querySelector('.info .person');
    let profileImage = personInfo.querySelector('img');
    let userName = personInfo.querySelector('a');
    let postDesc = postClone.querySelector('.post_desc');
    let descUser = postDesc.querySelector('a');
    let descText = postDesc.querySelector('.post_text span')
    let more = postClone.querySelector('.more')
    let like = postClone.querySelector('.icons .like');
    like.setAttribute('data-post', data.id)

    postClone.setAttribute('data-post', data.id);
    profileImage.src = data.owner.profile_image;
    userName.textContent = data.owner.username;
    descUser.textContent = data.owner.username;
    descText.textContent = data.text
    image.src = data.image;

    post.parentNode.insertBefore(postClone, post.nextSibling)
    deletePost(more)
    postClone.classList.remove('hide')
}

function addPostProfile(data) {
    let postsSection = document.getElementById('posts_sec');
    let div = document.createElement('div');
    div.className = 'item';
    let image = document.createElement('img');
    image.src = data.image;
    image.className = 'img-fluid item_img';
    div.appendChild(image);
    postsSection.prepend(div);

}
//post published
function addPost(data) {
    //add post in home 
    let pathName = window.location.pathname;
    if (pathName == '/') {
        addPostHome(data)
    }
    if (pathName == '/profile/') {
        addPostProfile(data)
    }


}

function completed(imageFile) {
    const share_btn_post = document.querySelector(".share_btn_post");
    const post_published = document.querySelector('.post_published');
    const modal_dialog = document.querySelector("#create_modal .modal-dialog");
    share_btn_post.addEventListener("click", async function() {
        const formData = new FormData();
        let description = document.getElementById('description');
        formData.append('image', imageFile);
        formData.append('text', description.value);

        const accessToken = await getToken()

        const response = await fetch('http://localhost:8000/api/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            body: formData
        })
        const data = await response.json()

        if (response.ok) {
            modal_dialog.classList.add("modal_complete");
            post_published.classList.remove("hide_img");
            share_btn_post.innerHTML = ""
            addPost(data)
            addEventListeners()
        }


    })
}

function deletePost(element) {

    element.addEventListener('click', (event) => {
        let deleteBtn = document.getElementById('delete-post')
        let post = event.target.closest('.post');
        let postId = post.getAttribute('data-post')

        deleteBtn.addEventListener('click', async () => {
            const accessToken = await getToken()
            const response = await fetch(`http://localhost:8000/api/post/${postId}`, {
                method: 'Delete',
                headers: {
                    Authorization: `Bearer ${accessToken}`
                }

            })
            if (response.ok) {

                post.remove()
                let btnClose = document.querySelector('#submit_delete_modal .btn-close');

                btnClose.click()

            }
        })

    })
}

document.querySelectorAll('.more').forEach((element) => {
    deletePost(element)
})

document.querySelector('#create-btn').addEventListener('click', (event) => {
    event.preventDefault();

    let modal = document.querySelector('#create_modal_clone')
    let modalBack = document.createElement('div')
    modalBack.className = 'modal-backdrop fade show'
    document.body.appendChild(modalBack)
    let modalClone = modal.cloneNode(true)
    modalClone.id = 'create_modal'
    modal.parentNode.insertBefore(modalClone, modal)
    modalClone.classList.add('show')
    modalClone.style.display = 'block'

    const form = document.querySelector('#upload-form');


    let next_btn_post = document.querySelector(".next_btn_post");
    next_btn_post.addEventListener('click', handleNext);
    form.addEventListener('change', handleSubmit);
    hideModal(modalClone)

})