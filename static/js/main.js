import { getToken, login } from './get-token.js'
"use strict"
/***************Post**************************/
const posts = document.querySelector(".posts");
const baseUrl = window.location.origin
let pathName = window.location.pathname;
let currentUser = document.getElementById('owner').textContent.match(/\w+(?=")/)




/**************************comments **************************/

//comments

function hideShowReply(modalBody, post = false, comments = null, response = null) {

    if (post) {
        //show replies of post that write reply
        let seeComment = comments.querySelector('.comment .see_comment');
        let replies = comments.querySelectorAll('.responses');
        let showComment = seeComment.querySelector('.show_c');
        let hideComment = seeComment.querySelector('.hide_com')
        replies.forEach(item => {
            item.classList.remove('hide')
            showComment.classList.add('hide');
            hideComment.classList.remove('hide')
        })
        let previousReplies = showComment.children[1].textContent
        showComment.children[1].textContent = Number(previousReplies) + 1;
        seeComment.addEventListener('click', () => {

            response.classList.toggle('hide')

        })


    } else {
        //add toggle to showComment and hideComment to display and hide replies of comment
        let comments = modalBody.querySelectorAll('.comments')
        comments.forEach(element => {

            let seeComment = element.querySelector('.comment .see_comment');
            let replies = element.querySelectorAll('.responses')
            let showComment = seeComment.querySelector('.show_c');
            let hideComment = seeComment.querySelector('.hide_com')
            showComment.children[1].textContent = replies.length
            seeComment.addEventListener('click', () => {
                showComment.classList.toggle('hide')
                hideComment.classList.toggle('hide')
                replies.forEach(item => {
                    item.classList.toggle('hide')
                })
            })

        })
    }
}

let hideInsideModal=null
function hideModal(event, cloneModal, remove = false, element = false) {
    console.log('hidemodal function')
    let modalId = cloneModal.getAttribute('id')
    let modalContainer = document.getElementById(modalId)
    //add event listener when click on screen to close modal    



    let closeBtn;
    let cancelBtn
    if (modalContainer != null) {
        closeBtn = modalContainer.querySelector('.btn-close');
        cancelBtn = modalContainer.querySelector('.cancel')


    }

    let moreCondition
    
    if (element != false) {
        
        moreCondition = element != event.target
    } else {
        moreCondition = true
    }

    let condition = event.target == closeBtn || event.target == cancelBtn || !event.target.closest('.modal-content') && modalContainer != null && moreCondition;
    let modalBack = document.querySelector('.modal-backdrop')


    if (condition && remove == true) {

        if (modalBack) {

            modalBack.remove();
        }
        modalContainer.remove();

    } else if (condition) {
        if(modalBack){

        modalBack.remove()
        }
        modalContainer.classList.remove('show')
        modalContainer.style.display = 'none'
    }else{
        document.removeEventListener('click',hideInsideModal)
        hideInsideModal=(e)=>hideModal(e, cloneModal, remove, element )
        document.addEventListener('click',hideInsideModal)
    }
    
}

function replyListener(modalBody, replyBtn, replyTO, commentUser, mainComment) {

    if (currentUser != null) {

        let modalContent = modalBody.closest('.modal-content')
        replyBtn.addEventListener('click', () => {



            let input = modalContent.querySelector('input')



            input.focus()
            input.value = `@${commentUser} `
            input.setAttribute('data-mainComment', mainComment);
            input.setAttribute('data-replyTo', replyTO);

        })
    }
}


function createCommentElement(modalBody, commentsSection, item, postId, post = false) {



    if (item.main_comment == null) {
        let comment = commentsSection.cloneNode(true)
        comment.className = 'comments'
        comment.setAttribute('data-comment', item.id)
        comment.setAttribute('data-is_user_comment', item.is_user_comment)


        let content = comment.querySelector('.content')

        let time = content.querySelector('span');
        time.textContent = item.created;

        let userName = content.querySelector('h4');
        userName.textContent = item.author.username;

        let image = comment.querySelector('.comment img')
        image.src = item.author.profile.profile_image

        let contentText = content.querySelector('p');
        contentText.textContent = item.comment;

        modalBody.append(comment)

        let replyBtn = comment.querySelector('.reply-btn');
        let replyTO = item.id
        let commentUser = item.author.username;
        let mainComment = item.id
        if (window.screen.width <= 498 || pathName == '/') {

            let postElement = document.querySelector(`[data-post="${postId}"]`)
            let viewComments = postElement.querySelector('.view-comments')
            if (post && viewComments.children.length == 0) {
                let a = document.createElement('a');
                a.classList.add('gray')
                a.href = '#'
                a.innerHTML = 'View all <span>1</span> comments'
                viewComments.append(a)
            } else if (post) {

                let span = viewComments.querySelector('span')
                span.textContent = Number(span.textContent) + 1;
            }
        }
        if (post) {
            hideShowReply(modalBody)

        }
        replyListener(modalBody, replyBtn, replyTO, commentUser, mainComment)

        if (currentUser == item.author.username) {

            deleteComment(comment, postId)
        } else {
            let dropDown = comment.querySelector('#drop-down')
            dropDown.remove()
        }

        commentLikeInfo(comment, item.like_info)
        let likeCommentDiv = comment.querySelector('.like')

        likeCommentDiv.addEventListener('click', () => {

            if (currentUser != null) {

                likeComment(comment, item.like_info)
            }

        })
    } else {
        //reply 
        //find comment that reply to that

        let comment = modalBody.querySelector(`.comments[data-comment="${item.main_comment}"]`)
        let show_reply = comment.querySelector('.see_comment')

        let responsesClone = comment.querySelector('.responses-clone');
        let response = responsesClone.cloneNode(true)

        //if create comment or reply on comment be true ,when creating reply response will be displayed
        if (post) {

            response.className = 'responses'
        } else {
            response.className = 'responses hide'
        }
        response.setAttribute('data-comment', item.id)
        response.setAttribute('data-is_user_comment', item.is_user_comment)
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
        let replyBtn = response.querySelector('.reply-btn');
        let replyTO = item.id
        let commentUser = item.author.username;

        let mainComment = item.main_comment
        replyListener(modalBody, replyBtn, replyTO, commentUser, mainComment)
        let postElement = document.querySelector(`[data-post="${postId}"]`)
        let viewComments = postElement.querySelector('.view-comments')
        if (post) {
            hideShowReply(modalBody, post, comment, response)
            let span = viewComments.querySelector('span')
            span.textContent = Number(span.textContent) + 1;
        }
        let responseComment = true
        if (currentUser == item.author.username) {

            deleteComment(response, postId)
        } else {
            let dropDown = response.querySelector('#drop-down')
            dropDown.remove()
        }

        commentLikeInfo(response, item.like_info)
        let likeCommentDiv = response.querySelector('.like')
        likeCommentDiv.addEventListener('click', () => {
            if (currentUser != null) {

                likeComment(response, item.like_info)
            } else {

            }

        })
    }
}

let hideCommentModal = null
async function getComments(modalClone, postId) {


    let modalBody = modalClone.querySelector('.comment-body')
    let commentsSection = modalBody.querySelector('.comments-clone')
    // const accessToken = await getToken()
    let response;
    if (currentUser != null) {
        let accessToken = await getToken()
        response = await fetch(`http://localhost:8000/api/post/${postId}/comments`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },

        })
    } else {

        response = await fetch(`http://localhost:8000/api/post/${postId}/comments`, {
            method: 'GET',
            // headers: {
            //     'Authorization': `Bearer ${accessToken}`
            // },

        })
    }
    const data = await response.json()

    if (response.ok) {

        if (data.length > 0) {

            data.forEach(item => {

                //comment not reply to comment
                //clone comments and use that
                createCommentElement(modalBody, commentsSection, item, postId)
            })
        } else {
            let empty = document.createElement('div')
            empty.className = 'empty'
            empty.textContent = 'No comments yet!'
            modalBody.append(empty)
        }
        document.removeEventListener('click', hideCommentModal)
        hideCommentModal = (e) => hideModal(e, modalClone, true)
        document.addEventListener('click', hideCommentModal,{once:true})
        hideShowReply(modalBody)
    }
}

//display comment modal by click on message buttons

function messageAddEvnetListener(messageElement) {

    messageElement.forEach(element => {
        element.addEventListener('click', (event) => {
            event.preventDefault();
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

            writeComment(modalClone, input, postId)


        })
    })
}




//comment


//get value of input in comment modal 
//pass values to postComment 
let commentForm = null

function writeComment(modalClone, input, postId) {
    if (input != null) {
        let form = input.closest('form')

        form.removeEventListener('submit', commentForm)

        commentForm = function() {
            event.preventDefault()
            let inputValue = input.value;
            let targetUser = inputValue.match(/@\w+\s/)
            let comment = inputValue.replace(/@\w+\s/, '');
            let replyTO = input.getAttribute('data-replyTo');
            let mainComment = input.getAttribute('data-mainComment');
            if (targetUser == null) {
                replyTO = null;
                mainComment = null;
            }

            postComment(modalClone, postId, comment, replyTO, mainComment)

        }
        form.addEventListener('submit', commentForm)
    }

}

//fetch post comment
//then use data that recieved pass in createCommentElement function
async function postComment(modalClone, postId, comment, replyTO, mainComment) {
    let formData = new FormData()

    formData.append('comment', comment)
    if (replyTO != null) {
        formData.append('parent', replyTO)

    }
    if (mainComment != null) {
        formData.append('main_comment', mainComment)

    }
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
        let modalBody = modalClone.querySelector('.modal-body');

        let commentSection = modalBody.querySelector('.comments-clone')
        let post = true;
        if (document.contains(document.querySelector('.empty'))) {
            document.querySelector('.empty').remove()
        }
        createCommentElement(modalBody, commentSection, item, postId, post)


    }
}

//delete comment
async function fetechDeleteComment(comment, postId, responseComment) {

    const modalBody = comment.closest('.modal-body')
    const accessToken = await getToken();
    const commentId = comment.getAttribute('data-comment');
    const response = await fetch(`http://localhost:8000/api/comment/${commentId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    })

    if (response.ok) {

        let postElement = document.querySelector(`[data-post="${postId}"]`)
        let viewComments = postElement.querySelector('.view-comments')
        comment.remove()
        let comments = modalBody.querySelectorAll('.comments')

        if (!responseComment && comments.length == 0) {
            let empty = document.createElement('div')
            empty.className = 'empty'
            empty.textContent = 'No comments yet!'
            modalBody.append(empty)
            viewComments.textContent = ''

        } else {
            let span = viewComments.querySelector('span')
            span.textContent = Number(span.textContent) - 1;

        }
    }
}

function deleteComment(comment, postId, responseComment = false) {

    let deleteComment = comment.querySelector('.delete-comment')
    let dropDownContent = comment.querySelector('.drop-down-content')
    deleteComment.addEventListener('click', () => {
        dropDownContent.classList.toggle('show-drop')
    })
    window.addEventListener('click', (event) => {
        if (event.target == comment.querySelector('.delete-btn-comment')) {
            event.preventDefault()
            fetechDeleteComment(comment, postId, responseComment)
        }
        if (!event.target.matches('.delete-comment')) {
            dropDownContent.classList.remove('show-drop')
        }
    })
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
    let post = document.querySelector('.post-clone');
    let postClone = post.cloneNode(true);
    postClone.className = 'post'
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
    addEventListeners(postClone)
}

function addPostProfile(data, saved = false) {
    let postsSection;
    if (saved) {
        postsSection = document.getElementById('saved_sec');


    } else {

        postsSection = document.getElementById('posts_sec');
    }
    let div = document.createElement('div');
    div.className = 'item';
    div.setAttribute('data-post', data.id)
    let image = document.createElement('img');
    image.src = data.image;
    image.className = 'img-fluid item_img';
    div.appendChild(image);
    if (saved) {

        postsSection.append(div);
    } else {
        postsSection.prepend(div);

    }

    let generalInfo = document.querySelector('.profile_info .general_info')

    let postInfo = generalInfo.children[0].querySelector('span')
    let divs = [div]
    postInfo.textContent = Number(postInfo.textContent) + 1

    profileDetailPost(divs)

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
        addPostHome(data)
    }


}

//fetch post and recieved data if response be ok ,pass data to addPost function
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

        }


    })
}

let deletePostCallBack = null
let fetchDeletePost = null

function deletePost(element, profile = false, deleteBtn = false) {
    let deleteModalBtn = document.getElementById('delete_modal')
    let submitDeleteModal = document.getElementById('submit_delete_modal')

    element.removeEventListener('click', deletePostCallBack)
    deletePostCallBack = function() {

        //delebtn inserted to deletePost function in post detail profile

        if (deleteBtn == false) {
            deleteBtn = document.getElementById('delete-post')
        }

        deleteModalBtn.addEventListener('click', (event) => {
            event.stopPropagation()
            let moreModal = document.getElementById('more_modal')
            moreModal.classList.remove('show')
            moreModal.style.display = 'none'
            submitDeleteModal.classList.add('show')
            submitDeleteModal.style.display = 'block'

            document.removeEventListener('click', closeModal, )
            
            closeModal = (e) => hideModal(e, submitDeleteModal, false)
            console.log('submitdeletemodal')
            document.addEventListener('click', closeModal,{once:true})

        })
        let post = event.target.closest('.post');


        let postId = post.getAttribute('data-post');
        deleteBtn.removeEventListener('click', fetchDeletePost)

        fetchDeletePost = async function() {
            const accessToken = await getToken()
            const response = await fetch(`http://localhost:8000/api/post/${postId}`, {
                method: 'Delete',
                headers: {
                    Authorization: `Bearer ${accessToken}`
                }

            })
            if (response.ok) {
                if (profile) {
                    let item = document.querySelector(`.item[data-post="${postId}"]`)
                    item.remove()
                } else {

                    post.remove()
                }
                let btnClose = document.querySelector('#submit_delete_modal .btn-close');

                btnClose.click()

            }
        }
        deleteBtn.addEventListener('click', fetchDeletePost)
    }
    element.addEventListener('click', deletePostCallBack)
}



let hideCreateModal = null

function createPostModal() {
    event.preventDefault();
    event.stopPropagation()
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
    document.removeEventListener('click', hideCreateModal)
    hideCreateModal = (e) => hideModal(e, modalClone, true)
    document.addEventListener('click', hideCreateModal,{once:true})

}

if (currentUser != null) {

    document.querySelector('#create-btn').addEventListener('click', createPostModal)
    document.querySelector('#sm_create_modal').addEventListener('click', createPostModal)
}
//like comment and reply

// like and dislike
async function likeComment(div, like_info) {

    const likeDiv = div.querySelector('.like')
    const commentId = div.getAttribute('data-comment')
    let lovedImg = likeDiv.querySelector('.loved')
    let notLovedimg = likeDiv.querySelector('.not_loved')
    let p = likeDiv.querySelector('p')
    const accessToken = await getToken()

    let headers = { 'Authorization': `Bearer ${accessToken}` }

    if (like_info.is_liked) {

        const response = await fetch(baseUrl + `/api/comment/likes/${like_info.id}`, {
            method: "DELETE",
            headers: headers
        })

        if (response.ok) {
            like_info.is_liked = false
            lovedImg.classList.remove('display')
            notLovedimg.classList.remove('hide')
            p.textContent = Number(p.textContent) - 1


        }

    } else {

        const body = { 'comment': commentId }

        const response = await fetch(baseUrl + '/api/comments/likes/', {
            method: 'POST',
            headers: {
                'Authorization': headers.Authorization,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        })

        const data = await response.json()
        if (response.ok) {
            like_info.is_liked = true
            like_info.id = data.id
            lovedImg.classList.add('display')
            notLovedimg.classList.add('hide')
            p.textContent = Number(p.textContent) + 1
        }

    }
}

function commentLikeInfo(div, like_info) {
    let likeDiv = div.querySelector('.like')
    let lovedImg = likeDiv.querySelector('.loved')
    let notLovedimg = likeDiv.querySelector('.not_loved')
    let p = likeDiv.querySelector('p')
    p.textContent = like_info.like_count
    if (like_info.is_liked) {
        lovedImg.classList.add('display')
        notLovedimg.classList.add('hide')
    }

}




//**********like post**************
// like and dislike
let counter = 0
async function like(div) {
    counter += 1

    if (currentUser != null) {

        const dataType = div.getAttribute('data-type');

        const dataPost = div.getAttribute('data-post');
        const dataLike = div.getAttribute('data-like');


        const accessToken = await getToken()
        let headers = { 'Authorization': `Bearer ${accessToken}` }


        if (dataType === 'True') {

            const response = await fetch(baseUrl + `/api/like/${dataLike}`, {
                method: "DELETE",
                headers: headers
            })


            if (response.ok) {

                let post = div.closest('.post');
                let liked = post.querySelector('.liked')
                let span = liked.querySelector('span');
                let likeCount = Number(liked.getAttribute('data-likeCount')) - 1;
                span.textContent = likeCount;
                liked.setAttribute('data-likeCount', likeCount)
                if (likeCount == 0) {
                    liked.textContent = ''
                } else if (likeCount == 1) {
                    span.nextSibling.textContent = ' like'
                }
                div.setAttribute('data-type', 'False')
                div.classList.remove('love')
                let not_loved = div.children[0];
                let loved = div.children[1];
                not_loved.classList.remove('hide_img')
                loved.classList.remove('display')



            }

        } else if (dataType === 'False') {
            const body = { 'post': dataPost }

            const response = await fetch(baseUrl + '/api/like/', {
                method: 'POST',
                headers: {
                    'Authorization': headers.Authorization,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            })


            if (response.ok) {


                const data = await response.json()


                div.setAttribute('data-type', 'True')
                let post = div.closest('.post')
                let liked = post.querySelector('.liked')
                let likeCount = Number(liked.getAttribute('data-likeCount')) + 1
                liked.setAttribute('data-likeCount', likeCount)

                if (likeCount == 1) {

                    liked.innerHTML = '<span>1</span> like'
                } else {
                    let span = liked.querySelector('span')
                    span.textContent = likeCount;
                    span.nextSibling.textContent = ' likes'
                }

                div.setAttribute('data-like', data.id)
                div.classList.add('love')
                let not_loved = div.children[0];
                let loved = div.children[1];
                not_loved.classList.add('hide_img')
                loved.classList.add('display')
            }

        }
    } else {

    }
}

//save post
let saveFetch

function savePost(element) {

    let postId = element.getAttribute('data-post')
    let saveIcon = element.querySelector('.save');
    if (saveIcon != null) {

        let saved = saveIcon.querySelector('.saved')
        let notSaved = saveIcon.querySelector('.not_saved')
        saveIcon.removeEventListener('click', saveFetch)
        saveFetch = async function() {
            let status = saveIcon.getAttribute('data-status');
            let savedId = saveIcon.getAttribute('data-saved')
            let accessToken = await getToken()
            if (status == 'True') {
                //delete post from saved posts

                const response = await fetch(baseUrl + `/api/saved/${savedId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,

                    },

                })
                if (response.ok) {
                    saveIcon.setAttribute('data-status', 'False');
                    saveIcon.setAttribute('data-saved', 'None')
                    saved.classList.add('hide')
                    notSaved.classList.remove('hide')
                }
            } else {
                //add post to saved posts
                const body = { 'post': postId }
                const response = await fetch(baseUrl + '/api/saved/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(body)
                })
                const data = await response.json()

                if (response.ok) {
                    saveIcon.setAttribute('data-status', 'True');
                    saveIcon.setAttribute('data-saved', data.id)
                    saved.classList.remove('hide')
                    notSaved.classList.add('hide')
                }
            }

        }
        saveIcon.addEventListener('click', saveFetch)
    }

}

function addEventListeners(newPost = false) {

    if (newPost) {
        //add listener post that be created

        let postLikeButton = newPost.querySelector('.like')
        postLikeButton.addEventListener('click', () => like(postLikeButton))

        let messageButtons = newPost.querySelectorAll('.chat button');
        let viewComments = newPost.querySelectorAll('.view-comments');

        messageAddEvnetListener(messageButtons)
        messageAddEvnetListener(viewComments)

        deletePost(newPost)
        savePost(newPost)

    } else {
        //for existing post add below listeners

        let posts = document.querySelectorAll('.posts .post')
        document.querySelectorAll('.like').forEach(div => {
            div.addEventListener('click', (event) => {
                like(div)

            })
        })

        let messageButtons = document.querySelectorAll('.chat button');
        let viewComments = document.querySelectorAll('.view-comments');

        //add listener to post  to user can comment on post or reply on comment
        messageAddEvnetListener(messageButtons)
        messageAddEvnetListener(viewComments)

        document.querySelectorAll('.more').forEach((element) => {

            deletePost(element)
        })

        //save post

        posts.forEach(div => {

            savePost(div)


        })
    }



}


if (pathName == '/') {

    addEventListeners()
}




//search

//search section 
async function searchUser(findDiv, searchValue) {

    const accessToken = await getToken()
    const response = await fetch(`http://localhost:8000/api/users/?search=${searchValue}`, {
        method: "GET",
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    })
    const datas = await response.json()
    if (response.ok) {

        let accountDiv = findDiv.querySelector('.account-clone');

        datas.forEach(data => {
            let account = accountDiv.cloneNode(true);
            account.className = 'account'

            let a = account.querySelector('a')
            a.href = `${baseUrl}/profile/${data.username}`
            let imageDiv = account.querySelector('.img');
            let image = document.createElement('img')
            image.src = data.profile_image
            imageDiv.append(image)

            let username = account.querySelector('.username')
            username.textContent = data.username;

            let name = account.querySelector('.name')
            name.textContent = data.first_name
            findDiv.append(account)
        })
    }
}

if (currentUser != null) {

    let search_icon = document.getElementById("search_icon");
    let search = document.getElementById("search");
    let findDiv = search.querySelector('.find')
    let searchForm = search.querySelector('form')
    let searchInput = search.querySelector('input');
    searchInput.addEventListener('input', event => {
        findDiv.querySelectorAll('.account').forEach(element => {
            element.remove()
        })

        const searchValue = event.target.value.trim();
        if (searchValue != '') {
            searchUser(findDiv, searchValue)
        } else {
            findDiv.querySelectorAll('.account').forEach(element => {
                element.remove()
            })
        }
    })
    searchForm.addEventListener('submit', event => {
        event.preventDefault();

    })

    search_icon.addEventListener("click", function() {


        search.classList.toggle("show");


    });
}

let notification = document.getElementById("notification");
let notification_icon = document.querySelectorAll(".notification_icon");
notification_icon.forEach((notif) => {
    notif.addEventListener('click', function() {
        notification.classList.toggle("show");
    })
})

//follow and unfollow
async function contact() {
    let btn = document.querySelector('.contact')
    let generalInfo = document.querySelector('.general_info');
    let followers = generalInfo.children[1].querySelector('span')
    let func = btn.getAttribute('data-btn');
    const accessToken = await getToken()

    if (func == 'unfollow' || func == 'requested') {


        const contactId = btn.getAttribute('data-contact');

        const response = await fetch(baseUrl + `/api/contact/${contactId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })

        if (response.ok) {
            if (func == 'unfollow') {

                btn.setAttribute('data-function', 'follow')
                btn.setAttribute('data-btn', 'follow')
                btn.textContent = 'follow'

                followers.textContent = Number(followers.textContent) - 1
            } else if (func == 'requested') {
                btn.setAttribute('data-function', 'follow')
                btn.setAttribute('data-btn', 'follow')
                btn.textContent = 'follow'
            }
        }
    } else if (func == 'follow') {
        let ownerProfile = btn.getAttribute('data-owner')
        let datas = { to_user: ownerProfile }
        const response = await fetch(baseUrl + `/api/contact/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'

            },
            body: JSON.stringify(datas)
        })

        const data = await response.json()
        if (response.ok) {
            btn.setAttribute('data-btn', 'unfollow')
            btn.setAttribute('data-contact', data.id)
            if (data.access) {

                btn.textContent = 'unfollow'
                followers.textContent = Number(followers.textContent) + 1
            } else {
                btn.textContent = 'requested'
                btn.setAttribute('data-btn', 'requested')
            }


        }
    }
}


if (document.contains(document.querySelector('.contact'))) {
    let contactBtn = document.querySelector('.contact')

    contactBtn.addEventListener('click', () => {



        contact()

    })
}

//logout
if (currentUser != null) {

    let logoutBtn = document.querySelector('.logout')
    let logoutForm = logoutBtn.querySelector('form')
    logoutBtn.addEventListener('click', event => {
        event.preventDefault();
        logoutForm.submit()

    })
}

///settings




if (pathName == '/settings/') {
    let tab = document.querySelector('.tab')
    let tabBtn = document.querySelectorAll('.tablinks')
    let user = document.getElementById('user').textContent
    let previousContent
    let previousBtn
    tabBtn.forEach(element => {
        let dataTab = element.getAttribute('data-tab');
        element.addEventListener('click', () => {
            editInfo(dataTab, user)
            if (previousBtn != null) {
                previousBtn.classList.remove('active')
            }
            previousBtn = element
            element.classList.add('active')
            showTab(element, dataTab)
        })
    })

    function showTab(element, dataTab) {
        if (previousContent != null) {

            previousContent.classList.add('hide')
        }
        let tabContent = document.getElementById(dataTab)
        previousContent = tabContent
        tabContent.classList.remove('hide')

        if (window.screen.width <= 498) {
            let tabContent = document.querySelector('.tab-content')
            element.classList.remove('active')
            tab.style.display = 'none'
            tabContent.style.display = 'block'
        }

    }

    let backBtn = document.querySelectorAll('.back')
    backBtn.forEach(element => {
        element.addEventListener('click', () => {
            let row = element.closest('.row')
            row.classList.add('hide')


            tab.style.display = 'block'
        })
    })
}

async function editInfo(dataTab, user) {
    let accessToken = await getToken()
    if (dataTab == 'edit-profile' || dataTab == 'personal-detail' || dataTab == 'account-privacy') {
        let response = await fetch(baseUrl + `/api/profiles/${user}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }

        })
        let data = await response.json()
        if (response.ok) {

            let name = document.getElementById('first_name')
            name.setAttribute('data-current', data.user.first_name)
            name.value = data.user.first_name

            let userName = document.getElementById('username')
            userName.setAttribute('data-current', data.user.username)
            userName.value = data.user.username

            let bio = document.getElementById('bio')
            bio.value = data.bio

            let profileImage = document.getElementById('profile_image')
            profileImage.src = data.profile_image

            let birthday = document.getElementById('birth_day')
            birthday.value = data.birth_day

            let email = document.getElementById('email')
            email.setAttribute('data-current', data.user.email)
            email.value = data.user.email

            let privateInput = document.getElementById('private')

            privateInput.checked = data.private
        }

        let profileForm = document.querySelector('.profile-form');
        profileForm.addEventListener('submit', async function(event) {
            event.preventDefault()
            let accessToken = await getToken()
            let username = document.getElementById('username')
            let name = document.getElementById('first_name')
            let bio = document.getElementById('bio')

            let currentUsername = username.getAttribute('data-current')
            let usernameValue = username.value
            let nameValue = name.value
            let bioValue = bio.value
            let userData = { username: usernameValue, first_name: nameValue }

            if (usernameValue == currentUsername) {
                delete userData.username
            }
            let body = { user: userData, bio: bioValue }


            let response = await fetch(baseUrl + `/api/profiles/${user}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'

                },
                body: JSON.stringify(body)
            })
            let data = await response.json()
            if (response.ok) {

                let messages = document.querySelector('#edit-profile .messages')
                let message = document.createElement('div')
                message.textContent = 'Saved successfully!'
                message.className = 'alert alert-success'
                messages.append(message)
                setTimeout(messageTimeOut, 10000, message)
            } else {

                if ('username' in data.user) {
                    let messages = document.querySelector('#edit-profile .messages')
                    let message = document.createElement('div')
                    message.textContent = data.user.username
                    message.className = 'alert alert-danger'
                    messages.append(message)
                    setTimeout(messageTimeOut, 10000, message)

                    username.value = currentUsername;
                }
            }


        })

        let imgBtn = document.getElementById('imgBtn')
        imgBtn.addEventListener('click', (event) => {
            event.preventDefault()
            let imageInput = document.getElementById('image-input')
            imageInput.click()
            imageInput.addEventListener('change', async function() {

                let formData = new FormData()
                let file = imageInput.files[0]
                formData.append('profile_image', file)
                let response = await fetch(baseUrl + `/api/profiles/${user}`, {
                    method: "PATCH",
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                    },
                    body: formData
                })
                let data = await response.json()
                if (response.ok) {
                    let messages = document.querySelector('#edit-profile .messages')
                    let message = document.createElement('div')
                    message.textContent = 'Saved successfully!'
                    message.className = 'alert alert-success'
                    messages.append(message)
                    setTimeout(messageTimeOut, 10000, message)
                } else {
                    let messages = document.querySelector('#edit-profile .messages')
                    let message = document.createElement('div')
                    if ('profile_image' in data) {

                        message.textContent = data.profile_image
                        message.className = 'alert alert-danger'
                        messages.append(message)
                        setTimeout(messageTimeOut, 10000, message)
                    }
                }
            })
        })

        //personal details
        let personalForm = document.querySelector('.personal-form')
        personalForm.addEventListener('submit', async function(event) {
            event.preventDefault()
            let birthday = document.getElementById('birth_day').value
            let email = document.getElementById('email').value
            let currentEmail = document.getElementById('email').getAttribute('data-current')
            let userData
            if (email != currentEmail) {
                userData = { 'email': email }
            }
            let body = { 'birth_day': birthday, 'user': userData }


            let response = await fetch(baseUrl + `/api/profiles/${user}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            })
            let data = await response.json()
            if (response.ok) {
                let messages = document.querySelector('#personal-detail .messages')
                let message = document.createElement('div')
                message.textContent = 'Saved successfully!'
                message.className = 'alert alert-success'
                messages.append(message)
                setTimeout(messageTimeOut, 10000, message)
            }

        })
    }

    if (dataTab == 'account-privacy') {
        let privateStatus = document.getElementById('private')
        privateStatus.addEventListener('change', async function() {
            let accessToken = await getToken()
            let bodyData = { 'private': privateStatus.checked }
            let response = await fetch(baseUrl + `/api/profiles/${user}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bodyData)
            })
            let data = await response.json()
            if (response.ok) {

            }
        })
    }

    if (dataTab == 'security') {
        let changePasswordForm = document.getElementById('change-password-form')

        changePasswordForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            let formData = new FormData(changePasswordForm);
            let body = JSON.stringify(Object.fromEntries(formData))
            let accessToken = await getToken()
            try {

                let response = await fetch(baseUrl + '/api/change-password/', {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: body
                })
                let data = await response.json()
                let messages = document.querySelector('#security .messages')
                messages.textContent = ''
                if (response.ok) {
                    let message = document.createElement('div')
                    message.textContent = 'password changed successfully!'
                    message.className = 'alert alert-success'
                    messages.append(message)
                    setTimeout(messageTimeOut, 10000, message)

                } else {


                    if ('non_field_errors' in data) {

                        data.non_field_errors.forEach(error => {
                            let message = document.createElement('div')
                            message.textContent = error
                            message.className = 'alert alert-danger'
                            messages.append(message)
                            setTimeout(messageTimeOut, 10000, message)
                        })
                    } else if ('old_password' in data) {
                        let message = document.createElement('div')
                        message.textContent = data.old_password
                        message.className = 'alert alert-danger'
                        messages.append(message)
                        setTimeout(messageTimeOut, 10000, message)
                    }

                }
                changePasswordForm.querySelectorAll('input').forEach(element => {
                    element.value = ''
                })
            } catch (error) {

            }
        })


    }
}

function messageTimeOut(element) {
    element.remove()
}

// follower and following list

function connectFunction(div, btn, func) {
    let relationId = div.getAttribute('data-relation')
    let followingCounter = document.querySelector('.general_info .connections[data-list="following"] span')
    let followerCounter = document.querySelector('.general_info .connections[data-list="follower"] span')


    btn.addEventListener('click', async function() {
        let accessToken = await getToken()

        let response = await fetch(baseUrl + `/api/contact/${relationId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })

        if (response.ok) {

            div.remove()
            if (func == 'following') {

                followingCounter.textContent = Number(followingCounter.textContent) - 1
            } else if (func == 'follower') {
                followerCounter.textContent = Number(followerCounter.textContent) - 1

            }
        }

    })
}
async function connectionList(queryType, username) {
    let connectionContainer = document.querySelector('.connection-container')
    connectionContainer.textContent = ''

    let owner = document.querySelector('.connections').getAttribute('data-owner')
    const accessToken = await getToken()
    const response = await fetch(`http://localhost:8000/api/users/?relation=${queryType}&owner=${username}`, {
        method: "GET",
        headers: {
            Authorization: `Bearer ${accessToken}`
        }
    })
    const datas = await response.json()

    if (response.ok) {

        datas.forEach(data => {

            let connectionList = document.createElement('div')
            connectionList.className = 'connection-list'
            connectionList.setAttribute('data-relation', data.relation)

            let link = document.createElement('a')
            link.href = `${baseUrl}/profile/${data.username}`

            let image = document.createElement('img')
            image.src = data.profile_image
            link.append(image)
            connectionList.append(link)

            let userInfo = document.createElement('div')
            userInfo.className = 'user-info'

            let username = document.createElement('p')
            username.className = 'username'
            username.textContent = data.username

            let name = document.createElement('p')
            name.className = 'name'
            name.textContent = data.first_name

            userInfo.append(username)
            userInfo.append(name)



            connectionList.append(userInfo)
            if (currentUser == owner) {

                let connectBtn = document.createElement('div')
                connectBtn.className = 'connect-button'

                let button = document.createElement('button')
                button.className = 'button-4'
                button.setAttribute('role', 'button')
                if (queryType == 'follower') {

                    button.textContent = 'remove'
                } else {
                    button.textContent = 'unfollow'
                }
                connectBtn.append(button)
                connectionList.append(connectBtn)
                connectFunction(connectionList, connectBtn, queryType)
            }
            connectionContainer.append(connectionList)

        })
    }
}

function profileDetailPost(elements) {
    let run = true
    let escapeDetailModal = null
    let closeDetailModal = null
    let toggleDetailMore = null
    let closeDetailMoreContent = null
    let likePostFunction = null
    elements.forEach(element => {
        element.addEventListener('click', async function(event) {

            event.stopPropagation()



            if (window.screen.width > 498) {

                let postId = element.getAttribute('data-post');
                let response;
                // let accessToken = await getToken()
                if (currentUser != null) {
                    let accessToken = await getToken()
                    response = await fetch(baseUrl + `/api/post/${postId}/`, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        }
                    })
                } else {

                    response = await fetch(baseUrl + `/api/post/${postId}/`, {
                        method: 'GET',
                        // headers: {
                        //     'Authorization': `Bearer ${accessToken}`
                        // }
                    })
                }
                let data = await response.json()
                let backDrop = document.querySelector('#backdrop')
                let favDialogClone = document.getElementById('favDialog-clone')
                let favDialog = favDialogClone.cloneNode(true)
                favDialog.setAttribute('id', 'favDialog')
                backDrop.append(favDialog)
                let container = favDialog.querySelector('.comment-container .post_desc')
                let post = favDialog.querySelector('.comment-container .post')
                let likeDiv = post.querySelector('.liked')
                let saveIcon = post.querySelector('.save')
                let likeSpan = likeDiv.querySelector('span')
                let likeDivIcon = post.querySelector('.icons .like')
                let loved = likeDivIcon.querySelector('.loved')
                let notLoved = likeDivIcon.querySelector('.not_loved')
                let postUser = post.querySelector('.post_desc p a')
                let postText = post.querySelector('.post_desc p span')
                let infoUser = post.querySelector('.info .person a')
                let infoUserImg = post.querySelector('.info .person img')
                let more = post.querySelector('.more')


                if (response.ok) {
                    infoUser.textContent = data.owner.username
                    infoUserImg.src = data.owner.profile_image
                    postUser.textContent = data.owner.username
                    postText.textContent = data.text

                    if (currentUser != data.owner.username && more != null) {
                        more.remove()
                    }

                    let dialogImg = favDialog.querySelector('.image-container img')
                    dialogImg.src = data.image
                    backdrop.style.display = 'block'
                    favDialog.style.display = 'block'

                    post.setAttribute('data-post', data.id)
                    let commentsClone = container.querySelector('.comments-clone').cloneNode(true)
                    let commentBody = container.querySelector('.comment-body')

                    commentBody.textContent = ''
                    commentBody.append(commentsClone)

                    //like section
                    likeDivIcon.setAttribute('data-post', data.id)


                    if (data.is_liked[0]) {

                        likeDivIcon.setAttribute('data-type', 'True')
                        likeDivIcon.setAttribute('data-like', data.is_liked[1])
                        loved.classList.add('display')
                        notLoved.classList.add('hide_img')


                    } else {
                        likeDivIcon.setAttribute('data-type', 'False')
                        loved.classList.remove('display')
                        notLoved.classList.remove('hide_img')


                    }

                    if (data.is_saved[0]) {

                        saveIcon.setAttribute('data-status', 'True');
                        saveIcon.setAttribute('data-saved', data.is_saved[1])
                        let savedImg = saveIcon.querySelector('.saved')
                        let notSavedImg = saveIcon.querySelector('.not_saved')
                        savedImg.classList.remove('hide')
                        notSavedImg.classList.add('hide')
                    } else {
                        saveIcon.setAttribute('data-status', 'False');
                        saveIcon.removeAttribute('data-saved')
                        let savedImg = saveIcon.querySelector('.saved')
                        let notSavedImg = saveIcon.querySelector('.not_saved')
                        savedImg.classList.add('hide')
                        notSavedImg.classList.remove('hide')
                    }
                    likeDiv.setAttribute('data-likeCount', data.is_liked[2])
                    if (likeSpan == null) {

                        likeSpan = document.createElement('span')
                        likeDiv.append(likeSpan)
                        if (data.is_liked[2] > 1) {
                            likeDiv.append(' likes')
                        } else {
                            likeDiv.append(' like')
                        }
                    }

                    likeSpan.textContent = data.is_liked[2]


                }

                getComments(favDialog, postId)

                //close detail post with escape btn on click on outside of modal
                document.removeEventListener('keyup', escapeDetailModal)

                escapeDetailModal = function(event) {

                    if (event.key == 'Escape') {
                        backdrop.style.display = 'none'
                        favDialog.remove()
                    }
                }
                document.addEventListener('keyup', escapeDetailModal)

                document.removeEventListener('click', closeDetailModal)
                closeDetailModal = function(event) {

                    if (!event.target.closest('#favDialog') && favDialog.style.display == 'block' && !event.target.closest('#confirm-delete')) {

                        backdrop.style.display = 'none'
                        favDialog.remove()
                    }
                }
                document.addEventListener('click', closeDetailModal)
                //endclose detail post with escape btn on click on outside of modal




                //display and hide dropdown and dropdown content for delete post
                let moreBtn = favDialog.querySelector('.more')
                let moreDropDown = moreBtn.querySelector('.drop-down-content')
                moreBtn.removeEventListener('click', toggleDetailMore)
                document.removeEventListener('click', closeDetailMoreContent)

                toggleDetailMore = function() { moreDropDown.classList.toggle('hide') }
                closeDetailMoreContent = function(event) {
                    if (event.target.closest('.drop-down-content') || !event.target.closest('.drop-down')) {

                        moreDropDown.classList.add('hide')

                    }
                }
                if (moreBtn != null) {
                    moreBtn.addEventListener('click', toggleDetailMore)
                    document.addEventListener('click', closeDetailMoreContent)
                }
                //end display and hide dropdown and dropdown content for delete post


                //like postdetail
                let postLikeButton = post.querySelector('.icons .like')




                postLikeButton.removeEventListener('click', likePostFunction)


                likePostFunction = function() { like(postLikeButton) }


                postLikeButton.addEventListener('click', likePostFunction)

                //end like postdetail


                postDetailListener(favDialog, data.id, likeDiv)



            } else {
                //for device screen width less than 498 display like home page

                let postId = element.getAttribute('data-post')
                let profileContainer = document.querySelector('.profile_container')
                profileContainer.style.display = 'none'
                let posts = document.querySelector('.posts')
                let post = posts.querySelector(`.post[data-post="${postId}"]`)

                posts.classList.remove('hide')
                post.scrollIntoView({ behavior: 'instant' });


                addEventListeners()


            }

        })

    })

}

function postDetailListener(element, postId, likeDiv) {

    let moreBtn = element.querySelector('.more')
    let post = element.querySelector('.post')


    //display confirm delete modal and hide it
    let confirmDeleteDiv = document.getElementById('confirm-delete')
    let confirmDelete = confirmDeleteDiv.querySelector('.delete')
    if (moreBtn != null) {

        let deleteBtn = moreBtn.querySelector('.delete-btn-post')
        deleteBtn.addEventListener('click', (event) => {
            event.preventDefault()
            event.stopPropagation()
            confirmDeleteDiv.style.display = 'block'

            document.addEventListener('click', (event) => {
                if (!event.target.closest('#confirm-delete') || event.target.closest('.cancel')) {
                    confirmDeleteDiv.style.display = 'none'
                }
            })

        })
    }
    let input = element.querySelector('input')

    deletePost(element, true, confirmDelete)


    writeComment(element, input, postId)
    savePost(post)

}


if (pathName.includes('profile')) {


    let connectionModal = document.getElementById('connection-modal')
    let modalTitle = connectionModal.querySelector('.modal-title')

    //display follower and followings

    document.querySelectorAll('.connections').forEach(element => {

        element.addEventListener('click', () => {
            let title = element.getAttribute('data-list')
            let username = element.getAttribute('data-owner')
            modalTitle.textContent = title
            if (currentUser != null) {


                connectionList(title, username)
            }

        })
    })


    //display detail of post with different style for different device size


    //for nested addeventlistener 


    let elements = document.querySelectorAll('.item')

    profileDetailPost(elements)



    //display saved posts
    let savedBtn = document.getElementById('pills-saved-tab');
    if (savedBtn != null) {
        savedBtn.addEventListener('click', async function() {


            const accessToken = await getToken()
            const response = await fetch(baseUrl + '/api/posts/saved/', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            })
            const datas = await response.json();
            if (response.ok) {
                let postsSection = document.getElementById('saved_sec');
                postsSection.textContent = ''
                datas.forEach(data => {
                    addPostProfile(data, true)
                })
            }
        })

    }
}




let notificationDiv = document.querySelector('#notification .notifications')
let notifs = notificationDiv.querySelectorAll('.notif')
notifs.forEach(element => {
    let confirm = element.querySelector('.confirm_follow')
    confirm.addEventListener('click', async function() {
        const accessToken = await getToken()

        const contactId = element.getAttribute('data-contact');
        let update = { access: true }
        const response = await fetch(baseUrl + `/api/contact/${contactId}/`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(update)

        })
        const data = await response.json()

        if (response.ok) {
            let btn = element.querySelector('.confirm_follow')
            let deleteBtn = element.querySelector('.delete_request')
            let desc = element.querySelector('.desc')
            btn.remove()
            if (!data.reverse_following) {

                let followBack = document.createElement('button')
                followBack.textContent = 'follow back'
                followBack.classList.add('follow_back', 'notif_btn')
                let followDiv = element.querySelector('.follow')
                followDiv.prepend(followBack)

                let to_user = element.getAttribute('data-from_user')
                let info = { to_user: to_user }
                followBack.addEventListener('click', async function() {
                    let datas = { to_user: to_user }
                    let resp = await fetch(baseUrl + `/api/contact/`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`,
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(info)

                    })
                    if (resp.ok) {
                        followBack.remove()

                        deleteBtn.remove()
                    }
                })
            } else {
                deleteBtn.remove()
            }
            desc.textContent = 'following you'

        }
    })


})


// report post
let closeMoreModal = null
let displayMoreModal = function(event,element) {
    event.stopPropagation()
    let postDiv=event.target.closest('.post')
    let postOwner=postDiv.getAttribute('data-owner')
    let objectId=postDiv.getAttribute('data-post')
    let modal = document.querySelector('#more_modal')
    let moreModal = document.querySelector('#more_modal .modal-dialog')
    
    modal.setAttribute('data-post',objectId)
    modal.setAttribute('data-owner',postOwner)
    modal.classList.add('show')
    modal.style.display = 'block'
    let modalBackDrop = document.createElement('div')
    modalBackDrop.classList.add('modal-backdrop', 'fade', 'show')
    document.body.append(modalBackDrop)

    document.removeEventListener('click', closeMoreModal, )
    closeMoreModal = (e) => hideModal(e, modal, false, element)
    console.log('what')
    document.addEventListener('click', closeMoreModal,{once:true})


}
let moreBtns = document.querySelectorAll('.info .more')
moreBtns.forEach(element => {
    let displayMoreModalFunction = (e) => displayMoreModal(e,element)
    element.addEventListener('click', displayMoreModalFunction)



})


let closeModal = null
let reportBtn = document.querySelector('.report_btn')
async function report(generalReport,postId,objectTyp,postOwner){
        const body = { 'content_type': objectTyp,'object_id':postId,'general_report':generalReport }
        let accessToken = await getToken()
        const response = await fetch(baseUrl + '/api/report/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        })
        const data=await response.json()
        if(response.ok){
            console.log('report submited')
                let reportModal=document.getElementById('report_post_modal')
                reportModal.remove()
                let stepMoreClone=document.getElementById('other_report_step-clone')
                let stepMore = stepMoreClone.cloneNode(true)
                stepMore.setAttribute('id', 'other_report_step')
                let otherSteps=stepMore.querySelector('.other-steps')

                let block=document.createElement('a')
                block.textContent=`block ${postOwner}`

                let unfollow=document.createElement('a')
                unfollow.textContent=`unfollow ${postOwner}`

                otherSteps.append(block)
                otherSteps.append(unfollow)
                stepMore.classList.add('show')
                stepMore.style.display = 'block'
                document.body.append(stepMore)
                document.removeEventListener('click', closeModal, )
                closeModal = (e) => hideModal(e, stepMore, true)
                document.addEventListener('click', closeModal,{once:true})
        }
}
async function fetchReports(postOwner,postId,reportModal){
    let accessToken = await getToken()
    let response = await fetch(`http://localhost:8000/api/reports/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            })
    let data=await response.json()
    if(response.ok){

        let reportListDiv=reportModal.querySelector('.report-list')
        data.forEach(link=>{
            console.log(link)
            let reportLink=document.createElement('a')
            reportLink.textContent=link.title
            reportLink.href='#'
            reportListDiv.append(reportLink)
            reportLink.addEventListener('click',(event)=>{
                event.stopPropagation()
                let objectTyp='post'
                report(link.id,postId,objectTyp,postOwner)

            })
        })
    }
}
reportBtn.addEventListener('click', (event) => {
    event.stopPropagation()

    let moreModal = document.getElementById('more_modal')
    
    let postId=moreModal.getAttribute('data-post')
    let postOwner=moreModal.getAttribute('data-owner')
    moreModal.classList.remove('show')
    moreModal.style.display = 'none'
    let reportModalClone = document.getElementById('report_post_modal-clone')
    let reportModal = reportModalClone.cloneNode(true)
    reportModal.setAttribute('id', 'report_post_modal')
    reportModal.classList.add('show')
    reportModal.style.display = 'block'
    fetchReports(postOwner,postId,reportModal)
    document.body.append(reportModal)
    console.log('reportbtn addEventListener')
    document.removeEventListener('click', closeModal, )
    closeModal = (e) => hideModal(e, reportModal, true)
    document.addEventListener('click', closeModal,{once:true})


})