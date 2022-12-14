function initializeModal(modalID, buttonID) {
    // Get the modal element
    var modal = document.getElementById(modalID);
  
    // Get the button that opens the modal
    var btn = document.getElementById(buttonID);
  
    // Get the <span> element that closes the modal
    var span = modal.querySelector('.close');
  
    // When the user clicks on the button, open the modal
    btn.addEventListener('click', function() {
      modal.style.display = "block";
    });
  
    // When the user clicks on <span> (x), close the modal
    span.addEventListener('click', function() {
      modal.style.display = "none";
    });
  
    // When the user clicks anywhere outside of the modal, close it
    window.addEventListener('click', function(event) {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    });
  }

  window.addEventListener('load', function() {
    initializeModal('teacherModal', 'addTeacher');
    initializeModal('studentModal', 'addStudent');
    initializeModal('subjectsModal', 'addSubjects');
    initializeModal('classModal', 'addGroup');
  });



