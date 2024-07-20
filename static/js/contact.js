import { getToken } from './get-token.js'

const baseUrl = window.location.origin
let contactForm=document.getElementById('contactForm')
contactForm.addEventListener('submit',async function(event){
	event.preventDefault()
	let alerts=document.querySelectorAll('.alert')
	alerts.forEach(element=>{
		element.remove()
	})
	let formData=new FormData(contactForm)
	let emailReg= /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
	let errors
	for(let pair of formData.entries()){
		if(pair[1]==''){
			errors=true
			let message=document.createElement('div')
			message.classList.add('alert')
			message.textContent=`${pair[0]} should not be empty`
			let inputContainer=document.querySelector(`.${pair[0]}`)
			console.log(inputContainer)
			inputContainer.append(message)
		}
		if(pair[0]=='email' && pair[1]!=''){
			if(pair[1].match(emailReg)){
				
			}else{
				errors=true
				let message=document.createElement('div')
				message.classList.add('alert')
				message.textContent=`not valid email`
				let inputContainer=document.querySelector(`.${pair[0]}`)
				console.log(inputContainer)
				inputContainer.append(message)
			}

		}
	}

	if(!errors){
		
		console.log(JSON.stringify(Object.fromEntries(formData)))
		let response = await fetch(`${baseUrl}/api/message/`,{
			method: 'POST',
			headers:{
				
				'Content-Type' : 'application/json'
			},
			body:JSON.stringify(Object.fromEntries(formData))
		})
		let data=await response.json()
		if(response.ok){
			let inputs=document.querySelectorAll('.inputs')
			inputs.forEach(element=>{
				console.log(element)
				element.value=''

			})
			let contactForm=document.querySelector('.contact-form')

			let successAlert=document.createElement('div')
			successAlert.classList.add('form-message-success')
			contactForm.prepend(successAlert)
			successAlert.textContent='Your message sent'
			setTimeout(()=>{
				successAlert.remove()
			},5000)
		}
	}
})