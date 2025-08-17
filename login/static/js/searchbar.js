document.addEventListener("DOMContentLoaded", ()=>{
    const searchInput=document.querySelector(".search-Input")

    searchInput.addEventListener("input", (event)=>{
        const input=event.target.value.trim().toLowerCase()
        Search(input)


    })


    function Search(input){
        const events_cont=document.querySelector(".webinar");
        const events =events_cont.querySelectorAll(".webinar-card");
        events.forEach(event => {
            const title= event.querySelector(".webinar-title").textContent.trim().toLowerCase();

            if (title.includes(input) || input==""){
                event.style.display="block";
            }else{
                event.style.display="none";
            }
            
        });
    }
})