function formModal(){
	const addButton=document.querySelector('.add-button');
	addButton.addEventListener('click',()=>{
		const modal=document.querySelector('.add-form');
		modal.style.display='block';
		window.addEventListener('mouseup',(event)=>{
			if (!event.target.closest('.add-form')){
				modal.style.display='none';
			}
		})
	})

}

formModal()