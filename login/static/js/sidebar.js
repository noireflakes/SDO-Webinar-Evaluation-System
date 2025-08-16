

document.addEventListener("DOMContentLoaded", ()=>{

  console.log("web loaded")
    let menuState=false
    const menu=document.querySelector(".menu-bar");
    const nav_menu=document.querySelector(".nav-menu-bar");
    const close_sb=document.querySelector(".close-sb");
    const sidebar= document.querySelector(".sidebar");

    if (close_sb){
      close_sb.addEventListener("click",()=>{
      CloseSidebar();

    })

    }


    sidebar.addEventListener("click", (event)=>{
      if (event.target.tagName.toLowerCase()==="a"){
        console.log("sidebar close")
        CloseSidebar();
      }
    })




    




    if (menu){
        menu.addEventListener("click",()=>{RightSidebarAni()})
    }else if(nav_menu) {
        nav_menu.addEventListener("click",()=>{LeftSidebarAni()})
    }



      function RightSidebarAni(){
        if(menuState){
          sidebar.style.animation="slideInLeft .5s ease-out forwards";
          document.body.style.overflow = "auto";
          menuState=false;
          console.log(`THE MENUSTATE IS ${menuState}`)
          
        }else{
          sidebar.style.animation="slideOutLeft .5s ease-in forwards";
          menuState=true;
          document.body.style.overflow = "hidden";
          console.log(`THE MENUSTATE IS ${menuState}`)
        }
      }

      function LeftSidebarAni(){
        if(menuState){
          sidebar.style.animation="slideInRight .5s ease-out forwards";
          document.body.style.overflow = "auto";
          menuState=false;
          console.log(`THE MENUSTATE IS ${menuState}`)
          
        }else{
          sidebar.style.animation="slideOutRight .5s ease-in forwards";
          menuState=true;
          document.body.style.overflow = "hidden";
          console.log(`THE MENUSTATE IS ${menuState}`)
        }
      }

      function CloseSidebar(){
        sidebar.style.animation="slideInLeft .5s ease-out forwards";
        menuState=true;
        document.body.style.overflow = "auto";
      }
    







})