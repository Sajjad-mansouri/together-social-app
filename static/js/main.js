import { getToken, login } from './get-token.js'
import { addEventListeners } from './form-modal.js'
/***************Post**************************/
const posts = document.querySelector(".posts");
const baseUrl = window.location.origin



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

function hideShowReply(modalBody,post=false,comments=null,response=null) {
   if(post){
        console.log('create with post')
        let seeComment=comments.querySelector('.comment .see_comment');
        let replies=comments.querySelectorAll('.responses');
        let showComment=seeComment.querySelector('.show_c');
        let hideComment=seeComment.querySelector('.hide_com')
        replies.forEach(item=>{
          item.classList.remove('hide')
          showComment.classList.add('hide');
          hideComment.classList.remove('hide')
        })
        let previousReplies=showComment.children[1].textContent
        showComment.children[1].textContent=Number(previousReplies)+1;
        seeComment.addEventListener('click',()=>{
          
            response.classList.toggle('hide')
          
        })


   }else{
      console.log('create with getComments')
      let comments=modalBody.querySelectorAll('.comments')
      comments.forEach(element=>{

        let seeComment=element.querySelector('.comment .see_comment');
        let replies=element.querySelectorAll('.responses')
        let showComment=seeComment.querySelector('.show_c');
        let hideComment=seeComment.querySelector('.hide_com')
        showComment.children[1].textContent=replies.length
        seeComment.addEventListener('click',()=>{
            showComment.classList.toggle('hide')
            hideComment.classList.toggle('hide')
          replies.forEach(item=>{
            item.classList.toggle('hide')
          })
        })

  })
   }
}
function hideModal(cloneModal) {

    window.addEventListener('click', event => {
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
function replyListener(replyBtn,replyTO,commentUser,mainComment){
  replyBtn.addEventListener('click',()=>{
    console.log('reply btn listener')
    let input=document.querySelector('#message_modal input')

    input.focus()
    input.value=`@${commentUser} `
    input.setAttribute('data-mainComment',mainComment);
    input.setAttribute('data-replyTo',replyTO);

  })
}


function createCommentElement(modalBody, commentsSection, item,postId,post=false) {
    console.log(item)
    if (item.main_comment == null) {
        let comment = commentsSection.cloneNode(true)
        comment.className = 'comments'
        comment.setAttribute('data-comment', item.id)
        comment.setAttribute('data-is_user_comment',item.is_user_comment)

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

        let replyBtn=comment.querySelector('.reply-btn');
        let replyTO=item.id
        let commentUser=item.author.username;
        let mainComment=item.id
        let postElement=document.querySelector(`[data-post="${postId}"]`)
        let viewComments=postElement.querySelector('.view-comments')
        if(post && viewComments.children.length==0){
            let a=document.createElement('a');
            a.classList.add('gray')
            a.href='#'
            a.innerHTML='View all <span>1</span> comments'
            viewComments.append(a)
        }else if(post){
            console.log(post)
            let span=viewComments.querySelector('span')
            span.textContent=Number(span.textContent)+1;
        }

        replyListener(replyBtn,replyTO,commentUser,mainComment)
        deleteComment(comment,postId)
        commentLikeInfo(comment,item.like_info)
        let likeCommentDiv=comment.querySelector('.like')
        likeCommentDiv.addEventListener('click',()=>{
            likeComment(comment,item.like_info)
        })
    } else {
        //reply 
        //find comment that reply to that
      
        let comment = modalBody.querySelector(`.comments[data-comment="${item.main_comment}"]`)
        let show_reply=comment.querySelector('.see_comment')
        
        let responsesClone = comment.querySelector('.responses-clone');
        let response = responsesClone.cloneNode(true)
        if(post){

        response.className = 'responses'
        }else{
          response.className = 'responses hide'
        }
        response.setAttribute('data-comment',item.id)
        response.setAttribute('data-is_user_comment',item.is_user_comment)
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
        let replyBtn=response.querySelector('.reply-btn');
        let replyTO=item.id
        let commentUser=item.author.username;

        let mainComment=item.main_comment
        replyListener(replyBtn,replyTO,commentUser,mainComment)
        let postElement=document.querySelector(`[data-post="${postId}"]`)
        let viewComments=postElement.querySelector('.view-comments')
        if(post){
          hideShowReply(modalBody,post,comment,response)
            let span=viewComments.querySelector('span')
            span.textContent=Number(span.textContent)+1;
        }
        let responseComment=true
        deleteComment(response,postId,responseComment)
        commentLikeInfo(response,item.like_info)
        let likeCommentDiv=response.querySelector('.like')
        likeCommentDiv.addEventListener('click',()=>{
            likeComment(response,item.like_info)
        })
    }
}

let messageButtons = document.querySelectorAll('.chat button');
let viewComments=document.querySelectorAll('.view-comments')
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
                createCommentElement(modalBody, commentsSection, item,postId)
            })
        } else {
          let empty=document.createElement('div')
          empty.className='empty'
          empty.textContent='No comments yet!'
            modalBody.append (empty)
        }
        hideModal(modalBody)
        hideShowReply(modalBody)
}
}
messageAddEvnetListener(messageButtons)
messageAddEvnetListener(viewComments)
function messageAddEvnetListener(messageElement){
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

        writeComment(input, postId)
       

    })
})
}




//write comment


async function postComment(postId, comment,replyTO,mainComment) {
    let formData = new FormData()
    formData.append('comment', comment)
    if(replyTO!=null){
    formData.append('parent',replyTO)

    }
    if(mainComment!=null){
    formData.append('main_comment',mainComment)

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
    console.log('item in postComment',item)
    if (response.ok) {
        let modalBody = document.querySelector('#message_modal .modal-body');
        console.log(modalBody)
        let commentSection = modalBody.querySelector('.comments-clone')
        let post=true;
        if(document.contains(document.querySelector('.empty'))){
          document.querySelector('.empty').remove()
        }
        createCommentElement(modalBody,commentSection,item,postId,post)
        

    }
}

function writeComment(input, postId) {
    let form = input.closest('form')

    form.addEventListener('submit', (event) => {
        event.preventDefault()
        let inputValue = input.value;
        let comment=inputValue.replace(/@\w+\s/,'');
        let replyTO=input.getAttribute('data-replyTo');
        let mainComment=input.getAttribute('data-mainComment');
        postComment(postId, comment,replyTO,mainComment)
    })



}

//delete comment
async function fetechDeleteComment(comment,postId,responseComment){
    console.log(comment)
    const modalBody=comment.closest('.modal-body')
    const accessToken = await getToken();
    const commentId=comment.getAttribute('data-comment');
    const response=await fetch(`http://localhost:8000/api/comment/${commentId}`,{
        method:'DELETE',
        headers:{
            'Authorization':`Bearer ${accessToken}`
        }
    })

    if(response.ok){
            console.log(postId)
            let postElement=document.querySelector(`[data-post="${postId}"]`)
            let viewComments=postElement.querySelector('.view-comments')
            comment.remove()
            let comments=modalBody.querySelectorAll('.comments')

            if(!responseComment && comments.length==0){
              let empty=document.createElement('div')
          empty.className='empty'
          empty.textContent='No comments yet!'
            modalBody.append (empty)
            viewComments.textContent=''

            }else{
                let span=viewComments.querySelector('span')
                span.textContent=Number(span.textContent)-1;

            }
    }
}
function deleteComment(comment,postId,responseComment=false) {
    console.log(postId)
    let deleteComment=comment.querySelector('.delete-comment')
    let dropDownContent=comment.querySelector('.drop-down-content')
    deleteComment.addEventListener('click',()=>{
        dropDownContent.classList.toggle('show-drop')
    })
    window.addEventListener('click',(event)=>{
        if(event.target==comment.querySelector('.delete-btn-comment')){
            event.preventDefault()
            fetechDeleteComment(comment,postId,responseComment)
        }
        if(!event.target.matches('.delete-comment')){
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

//like comment and reply

// like and dislike
async function likeComment(div,like_info) {

    const likeDiv=div.querySelector('.like')
    const commentId=div.getAttribute('data-comment')
    let lovedImg=likeDiv.querySelector('.loved')
    let notLovedimg=likeDiv.querySelector('.not_loved')
    let p=likeDiv.querySelector('p')
    const accessToken = await getToken()
    if (like_info.is_liked ) {

        const response = await fetch(baseUrl + `/api/comment/likes/${like_info.id}`, {
            method: "DELETE",
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })

        if (response.ok) {
            like_info.is_liked=false
            lovedImg.classList.remove('display')
            notLovedimg.classList.remove('hide')
            p.textContent=Number(p.textContent)-1


        }

    } else  {

        const body = { 'comment': commentId }

        const response = await fetch(baseUrl + '/api/comments/likes/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        })
        
        const data=await response.json()
        if (response.ok) {
            like_info.is_liked=true
            like_info.id=data.id
            lovedImg.classList.add('display')
            notLovedimg.classList.add('hide')
            p.textContent=Number(p.textContent)+1
        }

    }
}
function commentLikeInfo(div,like_info){
    let likeDiv=div.querySelector('.like')
    let lovedImg=likeDiv.querySelector('.loved')
    let notLovedimg=likeDiv.querySelector('.not_loved')
    let p=likeDiv.querySelector('p')
    p.textContent=like_info.like_count
    if(like_info.is_liked){
        lovedImg.classList.add('display')
        notLovedimg.classList.add('hide')
    }

}