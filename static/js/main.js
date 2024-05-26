import { getToken, login } from './get-token.js'

/***************Post**************************/
const posts = document.querySelector(".posts");
const baseUrl = window.location.origin



/**************************video**************************/

/**************************search+notif-section **************************/



/**************************icons+text change **************************/
//change the icon when the user click on it

//love btn




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

function hideShowReply(modalBody, post = false, comments = null, response = null) {
    if (post) {
        console.log('create with post')
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
        console.log('create with getComments')
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

function replyListener(replyBtn, replyTO, commentUser, mainComment) {
    replyBtn.addEventListener('click', () => {
        console.log('reply btn listener')
        let input = document.querySelector('#message_modal input')

        input.focus()
        input.value = `@${commentUser} `
        input.setAttribute('data-mainComment', mainComment);
        input.setAttribute('data-replyTo', replyTO);

    })
}


function createCommentElement(modalBody, commentsSection, item, postId, post = false) {
    let owner=document.getElementById('owner').textContent.match(/\w+(?=")/)
    if (item.main_comment == null) {
        let comment = commentsSection.cloneNode(true)
        comment.className = 'comments'
        comment.setAttribute('data-comment', item.id)
        comment.setAttribute('data-is_user_comment', item.is_user_comment)


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

        let replyBtn = comment.querySelector('.reply-btn');
        let replyTO = item.id
        let commentUser = item.author.username;
        let mainComment = item.id
        let postElement = document.querySelector(`[data-post="${postId}"]`)
        let viewComments = postElement.querySelector('.view-comments')
        if (post && viewComments.children.length == 0) {
            let a = document.createElement('a');
            a.classList.add('gray')
            a.href = '#'
            a.innerHTML = 'View all <span>1</span> comments'
            viewComments.append(a)
        } else if (post) {
            console.log(post)
            let span = viewComments.querySelector('span')
            span.textContent = Number(span.textContent) + 1;
        }

        replyListener(replyBtn, replyTO, commentUser, mainComment)

        if(owner==item.author.username){

            deleteComment(comment, postId)
        }else{
            let dropDown=comment.querySelector('#drop-down')
            dropDown.remove()
        }
        commentLikeInfo(comment, item.like_info)
        let likeCommentDiv = comment.querySelector('.like')
        likeCommentDiv.addEventListener('click', () => {
            likeComment(comment, item.like_info)
        })
    } else {
        //reply 
        //find comment that reply to that

        let comment = modalBody.querySelector(`.comments[data-comment="${item.main_comment}"]`)
        let show_reply = comment.querySelector('.see_comment')

        let responsesClone = comment.querySelector('.responses-clone');
        let response = responsesClone.cloneNode(true)
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
        replyListener(replyBtn, replyTO, commentUser, mainComment)
        let postElement = document.querySelector(`[data-post="${postId}"]`)
        let viewComments = postElement.querySelector('.view-comments')
        if (post) {
            hideShowReply(modalBody, post, comment, response)
            let span = viewComments.querySelector('span')
            span.textContent = Number(span.textContent) + 1;
        }
        let responseComment = true
        if(owner==item.author.username){

            deleteComment(response, postId)
        }else{
                    let dropDown=response.querySelector('#drop-down')
            dropDown.remove()
    }
        commentLikeInfo(response, item.like_info)
        let likeCommentDiv = response.querySelector('.like')
        likeCommentDiv.addEventListener('click', () => {
            likeComment(response, item.like_info)
        })
    }
}


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
                createCommentElement(modalBody, commentsSection, item, postId)
            })
        } else {
            let empty = document.createElement('div')
            empty.className = 'empty'
            empty.textContent = 'No comments yet!'
            modalBody.append(empty)
        }
        hideModal(modalBody)
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

            writeComment(input, postId)


        })
    })
}




//comment


//get value of input in comment modal 
//pass values to postComment 
function writeComment(input, postId) {
    let form = input.closest('form')

    form.addEventListener('submit', (event) => {
        event.preventDefault()
        let inputValue = input.value;
        let comment = inputValue.replace(/@\w+\s/, '');
        let replyTO = input.getAttribute('data-replyTo');
        let mainComment = input.getAttribute('data-mainComment');
        postComment(postId, comment, replyTO, mainComment)
    })

}

//fetch post comment
//then use data that recieved pass in createCommentElement function
async function postComment(postId, comment, replyTO, mainComment) {
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
    console.log('item in postComment', item)
    if (response.ok) {
        let modalBody = document.querySelector('#message_modal .modal-body');
        console.log(modalBody)
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
    console.log(comment)
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
        console.log(postId)
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
    console.log(postId)
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
    postClone.className='post'
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

function addPostProfile(data,saved=false) {
    let postsSection;
    if(saved){
    postsSection = document.getElementById('saved_sec');


    }else{

    postsSection = document.getElementById('posts_sec');
    }
    let div = document.createElement('div');
    div.className = 'item';
    let image = document.createElement('img');
    image.src = data.image;
    image.className = 'img-fluid item_img';
    div.appendChild(image);
    if(saved){

    postsSection.append(div);
}else{
    postsSection.prepend(div);

}

    let generalInfo=document.querySelector('.profile_info .general_info')
    console.log(generalInfo)
    let postInfo=generalInfo.children[0].querySelector('span')
    console.log(postInfo)
    postInfo.textContent=Number(postInfo.textContent)+1

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

function deletePost(element) {

    element.addEventListener('click', (event) => {
        let deleteBtn = document.getElementById('delete-post')
        let post = event.target.closest('.post');
        
        let postId = post.getAttribute('data-post');

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
async function likeComment(div, like_info) {

    const likeDiv = div.querySelector('.like')
    const commentId = div.getAttribute('data-comment')
    let lovedImg = likeDiv.querySelector('.loved')
    let notLovedimg = likeDiv.querySelector('.not_loved')
    let p = likeDiv.querySelector('p')
    const accessToken = await getToken()
    if (like_info.is_liked) {

        const response = await fetch(baseUrl + `/api/comment/likes/${like_info.id}`, {
            method: "DELETE",
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
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
                'Authorization': `Bearer ${accessToken}`,
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
async function like(div) {
    console.log('liked')
    const dataType = div.getAttribute('data-type');

    const dataPost = div.getAttribute('data-post');
    const dataLike = div.getAttribute('data-like');

    const accessToken = await getToken()
    if (dataType === 'True') {

        const response = await fetch(baseUrl + `/api/like/${dataLike}`, {
            method: "DELETE",
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        })
        console.log(response)
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
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        })
        console.log(response)

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
}

//save post
function savePost(element){
    
        let postId=element.getAttribute('data-post')
        let saveIcon=element.querySelector('.save');

        let saved=saveIcon.querySelector('.saved')
        let notSaved=saveIcon.querySelector('.not_saved')
        saveIcon.addEventListener('click',async function(){
            let status=saveIcon.getAttribute('data-status');
            let savedId=saveIcon.getAttribute('data-saved')
            let accessToken=await getToken()
            if (status=='True'){
                //delete post from saved posts

                const response=await fetch(baseUrl + `/api/saved/${savedId}`,{
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,

                    },
    
                        })
                if(response.ok){
                    saveIcon.setAttribute('data-status','False');
                    saveIcon.setAttribute('data-saved','None')
                    saved.classList.add('hide')
                    notSaved.classList.remove('hide')
                }
            }else{
                //add post to saved posts
                const body = { 'post': postId }
                const response=await fetch(baseUrl+'/api/saved/',{
                    method:'POST',
                    headers:{
                        'Authorization':`Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body:JSON.stringify(body)
                })
                const data=await response.json()
                console.log(data)
                if(response.ok){
                    saveIcon.setAttribute('data-status','True');
                    saveIcon.setAttribute('data-saved',data.id)
                    saved.classList.remove('hide')
                    notSaved.classList.add('hide')   
                }
            }
            
        })
    
}

function addEventListeners(newPost = false) {
    console.log(newPost)
    if (newPost) {
        let postLikeButton = newPost.querySelector('.like')
        postLikeButton.addEventListener('click', ()=>like(postLikeButton))

        let messageButtons = newPost.querySelectorAll('.chat button');
        let viewComments = newPost.querySelectorAll('.view-comments');

        messageAddEvnetListener(messageButtons)
        messageAddEvnetListener(viewComments)

        deletePost(newPost)
        savePost(newPost)

    } else {

        let posts=document.querySelectorAll('.post')
        document.querySelectorAll('.like').forEach(div => {
            div.addEventListener('click', (event) => {
                like(div)

            })
        })

        let messageButtons = document.querySelectorAll('.chat button');
        let viewComments = document.querySelectorAll('.view-comments');

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
console.log(window.location.pathname)
if(window.location.pathname=='/'){

    addEventListeners()
}

//saved post tab
console.log(window.location.pathname)
if(window.location.pathname=='/profile/'){
    let savedBtn=document.getElementById('pills-saved-tab');
    savedBtn.addEventListener('click',async function(){
        console.log(savedBtn)

        const accessToken=await getToken()
        const response=await fetch(baseUrl+'/api/posts/saved/',{
            method:'GET',
            headers:{
                'Authorization':`Bearer ${accessToken}`
            }
        })
        const datas=await response.json();
        if(response.ok){
            let postsSection = document.getElementById('saved_sec');
            postsSection.textContent=''
            datas.forEach(data=>{

                addPostProfile(data,true)
            })
        }
    })
}


//search

//search section 
async function searchUser(findDiv,searchValue){

    const accessToken=await getToken()
    const response=await fetch(`http://localhost:8000/api/users/?search=${searchValue}`, {
                        method: "GET",
                        headers: {
                            Authorization: `Bearer ${accessToken}`
                        }
                    })
    const datas=await response.json()
    if(response.ok){

        let accountDiv=findDiv.querySelector('.account-clone');
        datas.forEach(data=>{
            let account=accountDiv.cloneNode(true);
            account.className='account'

            let a=account.querySelector('a')
            a.href=`${baseUrl}/profile/${data.username}`
            let imageDiv=account.querySelector('.img');
            let image=document.createElement('img')
            image.src=data.profile_image
            imageDiv.append(image)

            let username=account.querySelector('.username')
            username.textContent=data.username;

            let name=account.querySelector('.name')
            name.textContent=data.first_name
            findDiv.append(account)
        })
    }
}


let search_icon = document.getElementById("search_icon");
let search = document.getElementById("search");

let searchForm=search.querySelector('form')
searchForm.addEventListener('submit',event=>{
    event.preventDefault();

})

search_icon.addEventListener("click", function() {

    let findDiv=search.querySelector('.find')
    search.classList.toggle("show");
    let searchInput=search.querySelector('input');
    searchInput.addEventListener('input',event=>{
         findDiv.querySelectorAll('.account').forEach(element=>{
                element.remove()
            })

        const searchValue=event.target.value.trim();
        if(searchValue!=''){
            searchUser(findDiv,searchValue)
        }else{
            findDiv.querySelectorAll('.account').forEach(element=>{
                element.remove()
            })
        }
    })

});

let notification = document.getElementById("notification");
let notification_icon = document.querySelectorAll(".notification_icon");
notification_icon.forEach((notif) => {
    notif.addEventListener('click', function() {
        notification.classList.toggle("show");
    })
})

//follow and unfollow
async function  contact(){
    let btn=document.querySelector('.contact')
    let generalInfo=document.querySelector('.general_info');
    let followers=generalInfo.children[1].querySelector('span')
    let func=btn.getAttribute('data-btn');
    const accessToken=await getToken()
    if (func=='unfollow'){

        
        const contactId=btn.getAttribute('data-contact');

        const response=await fetch(baseUrl+`/api/contact/${contactId}`,{
            method:'DELETE',
            headers:{
                'Authorization':`Bearer ${accessToken}`
            }
        })

        if (response.ok){
            btn.setAttribute('data-function','follow')
            btn.setAttribute('data-btn','follow')
            btn.textContent='follow'

            followers.textContent=Number(followers.textContent)-1
        }
    }else if(func=='follow'){
        let owner=btn.getAttribute('data-owner')
        let datas={to_user:owner}
        const response=await fetch(baseUrl+`/api/contact/`,{
            method:'POST',
            headers:{
                'Authorization':`Bearer ${accessToken}`,
                'Content-Type':'application/json'

            },
            body:JSON.stringify(datas)
        })

        const data=await response.json()
        if (response.ok){
            btn.setAttribute('data-btn','unfollow')
            btn.setAttribute('data-contact',data.id)
            btn.textContent='unfollow'


            followers.textContent=Number(followers.textContent)+1
        }
    }
}


if(document.contains(document.querySelector('.contact'))){
    let contactBtn=document.querySelector('.contact')
    
    contactBtn.addEventListener('click',()=>{
    console.log('listener')

            
            contact()
        
    })
}

//logout
let logoutBtn=document.querySelector('.logout')
let logoutForm=logoutBtn.querySelector('form')
logoutBtn.addEventListener('click',event=>{
    event.preventDefault();
    logoutForm.submit()

})

///settings



let pathName = window.location.pathname;
if(pathName=='/settings/'){
     let tab=document.querySelector('.tab')
        let tabBtn=document.querySelectorAll('.tablinks')
        let user=document.getElementById('user').textContent
        let previousContent
        let previousBtn
        tabBtn.forEach(element=>{
            let dataTab=element.getAttribute('data-tab');
            element.addEventListener('click',()=>{
                editInfo(dataTab,user)
                if(previousBtn!=null){
                    previousBtn.classList.remove('active')
                }
                previousBtn=element
                element.classList.add('active')
                showTab(element,dataTab)
            })
        })
        function showTab(element,dataTab){
            if(previousContent!=null){

            previousContent.classList.add('hide')
            }
            let tabContent=document.getElementById(dataTab)
            previousContent=tabContent            
            tabContent.classList.remove('hide')
            
            if (window.screen.width<=498){
                let tabContent=document.querySelector('.tab-content')
                element.classList.remove('active')
                tab.style.display='none'
                tabContent.style.display='block'
            }
            
        }

        let backBtn=document.querySelectorAll('.back')
        backBtn.forEach(element=>{
            element.addEventListener('click',()=>{
                let row=element.closest('.row')
                row.classList.add('hide')


                tab.style.display='block'
            })
        })
}

async function editInfo(dataTab,user){
    let accessToken=await getToken()
    if(dataTab=='edit-profile' || dataTab=='personal-detail' || dataTab=='account-privacy'){
        let response=await fetch(baseUrl+`/api/profiles/${user}`,{
            method:'GET',
            headers:{
                'Authorization':`Bearer ${accessToken}`,
            }

        })
        let data=await response.json()
        if(response.ok){
            console.log(data)
            let name=document.getElementById('first_name')
            name.setAttribute('data-current',data.user.first_name)
            name.value=data.user.first_name

            let userName=document.getElementById('username')
            userName.setAttribute('data-current',data.user.username)
            userName.value=data.user.username

            let bio=document.getElementById('bio')
            bio.value=data.bio

            let profileImage=document.getElementById('profile_image')
            profileImage.src=data.profile_image

            let birthday=document.getElementById('birth_day')
            birthday.value=data.birth_day

            let email=document.getElementById('email')
            email.setAttribute('data-current',data.user.email)
            email.value=data.user.email

            let privateInput=document.getElementById('private')
            console.log(`checked:${data.private}`)
            privateInput.checked=data.private
        }

        let profileForm=document.querySelector('.profile-form');
        profileForm.addEventListener('submit',async function(event){
            event.preventDefault()
            let accessToken=await getToken()
            let username=document.getElementById('username')
            let name=document.getElementById('first_name')
            let bio=document.getElementById('bio')
            
            let currentUsername=username.getAttribute('data-current')
            let usernameValue=username.value
            let nameValue=name.value
            let bioValue=bio.value
            let userData={username:usernameValue,first_name:nameValue}
            
            if(usernameValue==currentUsername){
                delete userData.username
            }
            let body={user:userData,bio:bioValue}

            console.log(body)
            let response=await fetch(baseUrl+`/api/profiles/${user}`,{
                method:'PATCH',
                headers:{
                    'Authorization':`Bearer ${accessToken}`,
                    'Content-Type':'application/json'
                    
                },
                body:JSON.stringify(body)
            })
            let data=await response.json()
            if (response.ok){

            }


        })

        let imgBtn=document.getElementById('imgBtn')
        imgBtn.addEventListener('click',(event)=>{
            event.preventDefault()
            let imageInput=document.getElementById('image-input')
            imageInput.click()
            imageInput.addEventListener('change',async function(){

                    let formData=new FormData()
                    let file = imageInput.files[0]
                    formData.append('profile_image', file)
                    let response=await fetch(baseUrl + `/api/profiles/${user}`, {
                        method: "PATCH",
                        headers: {
                            'Authorization': `Bearer ${accessToken}`,
                        },
                        body: formData
                    })
                    let data=await response.json()
                    if (response.ok){
                        let image=document.getElementById('profile_image')
                        image.src=data.profile_image
                        let messageDiv=document.querySelector('.message')
                        messageDiv.textContent='image uploaded'
                    }
            }
                )
        })

        //personal details
        let personalForm=document.querySelector('.personal-form')
        personalForm.addEventListener('submit',async function(event){
            event.preventDefault()
            let birthday=document.getElementById('birth_day').value
            let email=document.getElementById('email').value
            let currentEmail=document.getElementById('email').getAttribute('data-current')
            let userData
            if(email!=currentEmail){
                userData={'email':email}
            }
            let body={'birth_day':birthday,'user':userData}
            
            console.log(JSON.stringify(body))
            let response=await fetch(baseUrl+`/api/profiles/${user}`,{
                method:'PATCH',
                headers:{
                    'Authorization':`Bearer ${accessToken}`,
                    'Content-Type':'application/json'
                },
                body:JSON.stringify(body)
            })
            let data=await response.json()
            if (response.ok){
                console.log(data)
            }

        })
    }

    if(dataTab=='account-privacy'){
        let privateStatus=document.getElementById('private')
        privateStatus.addEventListener('change',async function(){
            let accessToken=await getToken()
            let bodyData={'private':privateStatus.checked}
            let response=await fetch(baseUrl+`/api/profiles/${user}`,{
                method:'PATCH',
                headers:{
                    'Authorization':`Bearer ${accessToken}`,
                    'Content-Type':'application/json'
                },
                body:JSON.stringify(bodyData)
            })
            let data=await response.json()
            if(response.ok){
                console.log('changed')
            }
        })
    }
}