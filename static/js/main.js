import { getToken, login } from './get-token.js'
import { addEventListeners } from './form-modal.js'
/***************Post**************************/
const posts = document.querySelector(".posts");




/**************************video**************************/
//play video onscroll
const videos = document.querySelectorAll("video");
const reels = document.querySelector(".reels");
window.addEventListener("scroll", function() {
    const scrollPosition = window.scrollY + window.innerHeight;
    videos.forEach((video, index) => {
        reels.children[index].removeAttribute("id");
        const videoPosition = video.getBoundingClientRect().top + video.offsetHeight / 2;
        if (scrollPosition > videoPosition && videoPosition > 0 && videoPosition <= video.offsetHeight) {
            video.play();
            reels.children[index].setAttribute("id", "video_play");
        } else {
            video.pause();
        }
    });
});

//play && pause && mute video
let video_container = document.querySelectorAll(".video");
video_container.forEach(function(item) {
    let video = item.children[0];
    //if the user click on the video pause it 
    let button_play = item.children[1].children[1];
    item.addEventListener("click", function() {
        if (button_play.classList.contains("opac_1")) {
            video.play();
        } else {
            video.pause();
        }
        button_play.classList.toggle("opac_1");
    });
    //if the user click the mute btn make the video mute
    let mute_btn = item.children[1].children[0];
    let volum_up = mute_btn.children[0];
    let volum_mute = mute_btn.children[1];
    mute_btn.addEventListener("click", function(e) {
        e.stopPropagation();
        if (!video.muted) {
            video.muted = true;
            volum_up.classList.add("hide_img");
            volum_mute.classList.add("display");
        } else {
            video.muted = false;
            volum_up.classList.remove("hide_img");
            volum_mute.classList.remove("display");
        }
    });
    //change the text follow ==> following and the opposite
    let follow = item.children[1].children[2].children[0].children[2];
    follow.addEventListener("click", function(e) {
        e.stopPropagation();
        follow.classList.toggle("following");
        if (follow.classList.contains("following")) {
            follow.innerHTML = "Following";
        } else {
            follow.innerHTML = "Follow";
        }

    });
});

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
let replay_com = document.querySelector(".comments .responses");
let show_replay = document.querySelector(".comments .see_comment");
let hide_com = document.querySelector(".comments .see_comment .hide_com");
let show_com = document.querySelector(".comments .see_comment .show_c");
if (replay_com) {
    replay_com.classList.add("hide");
    hide_com.classList.add("hide");
    show_replay.addEventListener("click", function() {
        replay_com.classList.toggle("hide");
        show_com.classList.toggle("hide");
        hide_com.classList.toggle("hide");
    });
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

//post published
function addPost(data){
  let post=document.querySelector('.post');
  let postClone=post.cloneNode(true);
  let image=postClone.querySelector('.image img');
  let personInfo=postClone.querySelector('.info .person');
  let profileImage=personInfo.querySelector('img');
  let userName=personInfo.querySelector('a');
  let postDesc=postClone.querySelector('.post_desc');
  let descUser=postDesc.querySelector('a');
  let descText=postDesc.querySelector('.post_text span')

  let like=postClone.querySelector('.icons .like');
  like.setAttribute('data-post',data.id)
  console.log(data)
  profileImage.src=data.owner.profile_image;
  userName.textContent=data.owner.username;
  descUser.textContent=data.owner.username;
  descText.textContent=data.text
  image.src=data.image;

  post.parentNode.insertBefore(postClone,post.nextSibling)
  postClone.classList.remove('hide')

}
function completed(imageFile) {
    const share_btn_post = document.querySelector(".share_btn_post");
    const post_published = document.querySelector('.post_published');
    const modal_dialog = document.querySelector("#create_modal .modal-dialog");
    share_btn_post.addEventListener("click", function() {
        const formData = new FormData();
        let description = document.getElementById('description')
        formData.append('image', imageFile)
        formData.append('text', description.value)
        console.log(description.value)
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
                        modal_dialog.classList.add("modal_complete");
                        post_published.classList.remove("hide_img");
                        share_btn_post.innerHTML = ""
                        return resp.json()

                    }
                })
                .then((data) => {
                    
                    let posts = document.querySelector('.posts')
                    let post = document.querySelector('.post')
                    let clonePost = post.cloneNode(true)
                    addPost(data)
                    addEventListeners()


                })
        })

    })
}


document.querySelector('#create-btn').addEventListener('click', (event) => {
    event.preventDefault();
    console.log('clicked')
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

    console.log('start')
    let next_btn_post = document.querySelector(".next_btn_post");
    next_btn_post.addEventListener('click', handleNext);
    form.addEventListener('change', handleSubmit);

})
window.addEventListener('mouseup', (event) => {
    if (document.contains(document.querySelector('.modal-backdrop'))) {

        if (!event.target.closest('.modal-content') && !event.target.closest('#create-btn')) {
            console.log('if condition')
            document.querySelector('.modal-backdrop').remove()
            document.querySelector('#create_modal').remove()


        }
    }
})