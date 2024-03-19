import { getToken } from './get-token.js'
export function imageUpload(btn) {
const user = document.querySelector('#user').textContent
    const imgInput = document.querySelector('input[name="profile_image"]')
    imgInput.click()

    const img = document.querySelector('img.profile_image')

    imgInput.addEventListener('change', (e) => {
        console.log('change')
        getToken().then((accessToken) => {
            const formData = new FormData()

            let file = imgInput.files[0]
            formData.append('profile_image', file)
            fetch(origin + `/api/profiles/${user}`, {
                    method: "PATCH",
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    console.log(data)
                    console.log(img)
                    img.src = data.profile_image

                })
                .catch(error => console.log(error))

        })

    })
}

export async function changeProfile(formData) {
    try {
        const user = document.querySelector('#user').textContent;
        const accessToken = await getToken();
        const response = await fetch(origin + `/api/profiles/${user}`, {
            method: "PATCH",
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type':'application/json'
            },
            body: formData
        })
        const data = await response.json()
        console.log(data)
        const navTab = document.querySelector('.nav-tabs')
        if (response.ok) {
            const message = document.createElement('div')
            message.className = 'message alert alert-success text-center'
            message.textContent = 'changed successfully'
            const userName = document.querySelector('.username')
            userName.textContent = '@' + data.username
            navTab.after(message)
            setTimeout(() => {
                message.remove()
            }, 5000)


        } else {
            const err = document.querySelector('.errors')
            console.log(err)
            if (err) {
                err.remove()
            }
            const errors = document.createElement('div')
            errors.className = 'errors alert alert-warning text-center'
            const ul = document.createElement('ul')
            errors.append(ul)
            for (const key in data) {
                const li = document.createElement('li')
                li.textContent = data[key]
                ul.append(li)
                console.log(key, data[key])
            }
            navTab.after(errors)
        }
    } catch (error) {
        console.log(error)
    }
}